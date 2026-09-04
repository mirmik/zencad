"""Stable, bounded inspection of the EvalCache computation DAG."""

from __future__ import annotations

from dataclasses import dataclass, replace
import inspect
import json
import math
from pathlib import Path
import re
import time
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from evalcache import EvaluationEventKind, Evaluator, Expression


GRAPH_SCHEMA = "zencad.computation_graph"
GRAPH_SCHEMA_VERSION = 1
DEFAULT_MAX_GRAPH_NODES = 4096
MAX_ARGUMENT_SUMMARY = 160
MAX_NODE_ARGUMENTS = 32
MAX_NODE_DEPENDENCIES = 256
_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")
_PACKAGE_ROOT = Path(__file__).resolve().parent


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _safe_error(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _safe_error(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe_error(item) for item in value]
    if isinstance(value, str):
        return _clip(value, 16_384)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return f"<{type(value).__module__}.{type(value).__qualname__}>"


def _clip(text: str, limit: int = MAX_ARGUMENT_SUMMARY) -> str:
    text = _ADDRESS.sub("0x…", text)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _literal_summary(value: Any, depth: int = 0) -> str:
    """Describe an argument without invoking arbitrary or address-bearing repr."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return format(value, ".12g")
    if isinstance(value, str):
        return _clip(json.dumps(value, ensure_ascii=False))
    if isinstance(value, bytes):
        return f"<bytes {len(value)}>"
    if isinstance(value, Path):
        return _clip(json.dumps(str(value), ensure_ascii=False))
    if isinstance(value, Expression):
        return "@" + value.digest[:12]
    if depth >= 2:
        return f"<{type(value).__name__}>"
    if isinstance(value, Mapping):
        if len(value) > 16:
            return f"<mapping {len(value)} items>"
        items = sorted(
            (
                _literal_summary(key, depth + 1),
                _literal_summary(item, depth + 1),
            )
            for key, item in value.items()
        )
        body = ", ".join(f"{key}: {item}" for key, item in items[:6])
        if len(items) > 6:
            body += f", … +{len(items) - 6}"
        return _clip("{" + body + "}")
    if isinstance(value, (list, tuple, set, frozenset)):
        if len(value) > 16:
            return f"<{type(value).__name__} {len(value)} items>"
        items = [_literal_summary(item, depth + 1) for item in value]
        if isinstance(value, (set, frozenset)):
            items.sort()
        body = ", ".join(items[:6])
        if len(items) > 6:
            body += f", … +{len(items) - 6}"
        left, right = ("[", "]") if isinstance(value, list) else ("(", ")")
        if isinstance(value, (set, frozenset)):
            left, right = ("{", "}")
        return _clip(left + body + right)
    return f"<{type(value).__module__}.{type(value).__qualname__}>"


def _dependencies(
    value: Any, *, limit: int = MAX_NODE_DEPENDENCIES
) -> tuple[set[str], bool]:
    if isinstance(value, Expression):
        return {value.digest}, False
    if isinstance(value, Mapping):
        found: set[str] = set()
        for key, item in value.items():
            for candidate in (key, item):
                dependencies, truncated = _dependencies(
                    candidate,
                    limit=max(0, limit - len(found)),
                )
                found.update(dependencies)
                if truncated or len(found) >= limit:
                    return found, True
        return found, False
    if isinstance(value, (list, tuple, set, frozenset)):
        found = set()
        for item in value:
            dependencies, truncated = _dependencies(
                item,
                limit=max(0, limit - len(found)),
            )
            found.update(dependencies)
            if truncated or len(found) >= limit:
                return found, True
        return found, False
    return set(), False


def _source_location() -> tuple[str, int] | None:
    frame = inspect.currentframe()
    try:
        frame = None if frame is None else frame.f_back
        while frame is not None:
            filename = Path(frame.f_code.co_filename).resolve()
            if (
                not filename.is_relative_to(_PACKAGE_ROOT)
                and "evalcache" not in filename.parts
            ):
                return str(filename), frame.f_lineno
            frame = frame.f_back
    finally:
        del frame
    return None


@dataclass(frozen=True, slots=True)
class GraphArgument:
    name: str
    summary: str
    dependencies: tuple[str, ...] = ()

    @property
    def literal(self) -> bool:
        return not self.dependencies

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True, slots=True)
class ComputationNode:
    node_id: str
    digest: str
    operation: str
    operation_version: str
    result_type: str
    dependencies: tuple[str, ...]
    arguments: tuple[GraphArgument, ...]
    evaluation: str
    cache: str
    duration_ms: float | None = None
    source_file: str | None = None
    source_line: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "digest": self.digest,
            "operation": self.operation,
            "operation_version": self.operation_version,
            "result_type": self.result_type,
            "dependencies": list(self.dependencies),
            "arguments": [argument.to_dict() for argument in self.arguments],
            "state": {
                "evaluation": self.evaluation,
                "cache": self.cache,
                "duration_ms": self.duration_ms,
                "error": self.error,
            },
            "source": (
                None
                if self.source_file is None
                else {"file": self.source_file, "line": self.source_line}
            ),
        }


@dataclass(frozen=True, slots=True)
class ComputationRoot:
    root_id: str
    node_id: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.root_id, "node": self.node_id}


@dataclass(frozen=True, slots=True)
class ComputationGraph:
    nodes: tuple[ComputationNode, ...]
    roots: tuple[ComputationRoot, ...]
    script_path: str | None = None
    execution_status: str = "success"
    execution_error: Mapping[str, Any] | None = None
    truncated: bool = False
    node_limit: int = DEFAULT_MAX_GRAPH_NODES
    schema_version: int = GRAPH_SCHEMA_VERSION

    @property
    def by_id(self) -> Mapping[str, ComputationNode]:
        return MappingProxyType({node.node_id: node for node in self.nodes})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": GRAPH_SCHEMA,
            "schema_version": self.schema_version,
            "status": self.execution_status,
            "script": None if self.script_path is None else {"path": self.script_path},
            "limits": {"max_nodes": self.node_limit, "truncated": self.truncated},
            "error": _plain(self.execution_error),
            "roots": [root.to_dict() for root in self.roots],
            "nodes": [node.to_dict() for node in self.nodes],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return (
            json.dumps(
                self.to_dict(),
                allow_nan=False,
                ensure_ascii=False,
                indent=indent,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ComputationGraph":
        if value.get("schema") != GRAPH_SCHEMA:
            raise ValueError("Unsupported computation graph schema")
        if value.get("schema_version") != GRAPH_SCHEMA_VERSION:
            raise ValueError("Unsupported computation graph schema version")
        nodes = []
        for item in value.get("nodes", ()):
            state = item.get("state") or {}
            source = item.get("source") or {}
            nodes.append(
                ComputationNode(
                    node_id=item["id"],
                    digest=item["digest"],
                    operation=item["operation"],
                    operation_version=item["operation_version"],
                    result_type=item["result_type"],
                    dependencies=tuple(item.get("dependencies", ())),
                    arguments=tuple(
                        GraphArgument(
                            argument["name"],
                            argument["summary"],
                            tuple(argument.get("dependencies", ())),
                        )
                        for argument in item.get("arguments", ())
                    ),
                    evaluation=state.get("evaluation", "not_evaluated"),
                    cache=state.get("cache", "unknown"),
                    duration_ms=state.get("duration_ms"),
                    source_file=source.get("file"),
                    source_line=source.get("line"),
                    error=state.get("error"),
                )
            )
        return cls(
            nodes=tuple(nodes),
            roots=tuple(
                ComputationRoot(item["id"], item["node"])
                for item in value.get("roots", ())
            ),
            script_path=(value.get("script") or {}).get("path"),
            execution_status=value.get("status", "success"),
            execution_error=value.get("error"),
            truncated=bool((value.get("limits") or {}).get("truncated", False)),
            node_limit=int(
                (value.get("limits") or {}).get("max_nodes", DEFAULT_MAX_GRAPH_NODES)
            ),
        )

    def filtered(
        self,
        *,
        roots: Iterable[str] = (),
        failed_path: bool = False,
        max_depth: int | None = None,
        hide_literals: bool = False,
    ) -> "ComputationGraph":
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        node_map = dict(self.by_id)
        selected_roots = list(self.roots)
        requested = tuple(roots)
        if requested:
            selected_roots = []
            missing = []
            roots_by_name = {root.root_id: root for root in self.roots}
            roots_by_node = {root.node_id: root for root in self.roots}
            for requested_root in requested:
                if requested_root in roots_by_name:
                    selected_roots.append(roots_by_name[requested_root])
                elif requested_root in roots_by_node:
                    selected_roots.append(roots_by_node[requested_root])
                elif requested_root in node_map:
                    selected_roots.append(
                        ComputationRoot(requested_root, requested_root)
                    )
                else:
                    missing.append(requested_root)
            if missing:
                raise ValueError("Unknown graph root(s): " + ", ".join(missing))

        allowed: set[str] = set()
        frontier = [(root.node_id, 0) for root in selected_roots]
        while frontier:
            node_id, depth = frontier.pop()
            if node_id in allowed or node_id not in node_map:
                continue
            allowed.add(node_id)
            if max_depth is None or depth < max_depth:
                frontier.extend(
                    (item, depth + 1) for item in node_map[node_id].dependencies
                )

        if failed_path:
            errors = {node.node_id for node in self.nodes if node.evaluation == "error"}
            if not errors:
                allowed.clear()
            else:
                reverse: dict[str, set[str]] = {}
                for node in self.nodes:
                    for dependency in node.dependencies:
                        reverse.setdefault(dependency, set()).add(node.node_id)
                causes = {
                    node_id
                    for node_id in errors
                    if not (set(node_map[node_id].dependencies) & errors)
                }
                path = set(causes)
                pending = list(causes)
                while pending:
                    node_id = pending.pop()
                    for parent in reverse.get(node_id, ()):
                        if parent not in path:
                            path.add(parent)
                            pending.append(parent)
                allowed &= path
            selected_roots = [
                root for root in selected_roots if root.node_id in allowed
            ]

        nodes = tuple(
            replace(
                node,
                dependencies=tuple(
                    item for item in node.dependencies if item in allowed
                ),
                arguments=tuple(
                    argument
                    for argument in node.arguments
                    if not (hide_literals and argument.literal)
                ),
            )
            for node in self.nodes
            if node.node_id in allowed
        )
        return replace(self, nodes=nodes, roots=tuple(selected_roots))

    def to_tree(self) -> str:
        node_map = dict(self.by_id)
        lines = [f"ZenCad computation graph v{self.schema_version}"]
        lines.append(
            f"nodes: {len(self.nodes)}; roots: {len(self.roots)}; status: {self.execution_status}"
        )
        if self.truncated:
            lines.append(f"warning: graph truncated at {self.node_limit} nodes")
        expanded: set[str] = set()

        def emit(node_id: str, prefix: str, branch: str) -> None:
            node = node_map.get(node_id)
            if node is None:
                lines.append(f"{prefix}{branch}<omitted {node_id[:12]}>")
                return
            shared = node_id in expanded
            state = node.evaluation
            cache = node.cache
            timing = "" if node.duration_ms is None else f" {node.duration_ms:.3f}ms"
            arguments = ""
            if node.arguments:
                arguments = (
                    " args("
                    + ", ".join(
                        f"{argument.name}={argument.summary}"
                        for argument in node.arguments
                    )
                    + ")"
                )
            lines.append(
                f"{prefix}{branch}{node.operation} [{state}; cache:{cache}{timing}] #{node.digest[:12]}"
                + (" (shared)" if shared else "")
                + arguments
            )
            if shared:
                return
            expanded.add(node_id)
            children = [item for item in node.dependencies if item in node_map]
            for index, dependency in enumerate(children):
                last = index == len(children) - 1
                emit(
                    dependency,
                    prefix + ("   " if branch else ""),
                    "└─ " if last else "├─ ",
                )

        for root in self.roots:
            lines.append(f"{root.root_id}:")
            emit(root.node_id, "", "")
        return "\n".join(lines)


class ComputationGraphRecorder:
    """Opt-in observer used by the isolated runner; never stores result values."""

    def __init__(
        self, *, max_nodes: int = DEFAULT_MAX_GRAPH_NODES, cache_enabled: bool = True
    ):
        if (
            not isinstance(max_nodes, int)
            or isinstance(max_nodes, bool)
            or max_nodes <= 0
        ):
            raise ValueError("max_nodes must be a positive integer")
        self.max_nodes = max_nodes
        self.cache_enabled = cache_enabled
        self.nodes: dict[str, dict[str, Any]] = {}
        self.roots: dict[str, str] = {}
        self.started: dict[str, int] = {}
        self.truncated = False

    def record_expression(
        self, expression: Expression, args: tuple[Any, ...], kwargs: Mapping[str, Any]
    ) -> None:
        if expression.digest in self.nodes:
            return
        if len(self.nodes) >= self.max_nodes:
            self.truncated = True
            return
        source = _source_location()
        values = [(f"arg[{index}]", item) for index, item in enumerate(args)]
        values.extend((f"kw.{name}", item) for name, item in sorted(kwargs.items()))
        if len(values) > MAX_NODE_ARGUMENTS:
            values = values[:MAX_NODE_ARGUMENTS]
            self.truncated = True
        arguments = []
        all_dependencies: set[str] = set()
        for name, value in values:
            found, truncated = _dependencies(value)
            dependencies = tuple(sorted(found))
            if truncated:
                self.truncated = True
            all_dependencies.update(dependencies)
            arguments.append(GraphArgument(name, _literal_summary(value), dependencies))
        self.nodes[expression.digest] = {
            "expression": expression,
            "arguments": tuple(arguments),
            "dependencies": tuple(sorted(all_dependencies)),
            "evaluation": "not_evaluated",
            "cache": (
                "not_cacheable"
                if not expression.cacheable
                else "unknown"
                if self.cache_enabled
                else "disabled"
            ),
            "duration_ms": None,
            "source": source,
            "error": None,
        }

    def event(self, event) -> None:
        node = self.nodes.get(event.expression_digest)
        if node is None:
            return
        now = time.perf_counter_ns()
        if event.kind is EvaluationEventKind.START:
            node["evaluation"] = "evaluating"
            self.started.setdefault(event.expression_digest, now)
        elif event.kind is EvaluationEventKind.MEMORY_HIT:
            node["cache"] = "memory_hit"
        elif event.kind is EvaluationEventKind.CACHE_HIT:
            node["cache"] = "hit"
        elif event.kind is EvaluationEventKind.CACHE_REJECTED:
            node["cache"] = "rejected"
        elif event.kind is EvaluationEventKind.CACHE_STORE:
            if node["cache"] not in {"hit", "memory_hit"}:
                node["cache"] = "miss"
        elif event.kind is EvaluationEventKind.FINISH:
            node["evaluation"] = "evaluated"
            if node["cache"] == "unknown":
                node["cache"] = "miss"
            started = self.started.get(event.expression_digest)
            if started is not None:
                node["duration_ms"] = round((now - started) / 1_000_000, 6)
        elif event.kind is EvaluationEventKind.ERROR:
            node["evaluation"] = "error"
            node["error"] = _clip(event.detail or "evaluation failed", 500)
            if node["cache"] == "unknown":
                node["cache"] = "miss"
            started = self.started.get(event.expression_digest)
            if started is not None:
                node["duration_ms"] = round((now - started) / 1_000_000, 6)

    def add_root(self, root_id: str, value: Any) -> None:
        state = getattr(value, "_state", value)
        if isinstance(state, Expression):
            self.roots[root_id] = state.digest
            if state.digest not in self.nodes:
                protected = set(self.roots.values())
                removable = sorted(set(self.nodes) - protected, reverse=True)
                if removable:
                    self.nodes.pop(removable[0])
                if len(self.nodes) < self.max_nodes:
                    self.nodes[state.digest] = {
                        "expression": state,
                        "arguments": (),
                        "dependencies": (),
                        "evaluation": "not_evaluated",
                        "cache": (
                            "not_cacheable"
                            if not state.cacheable
                            else "unknown"
                            if self.cache_enabled
                            else "disabled"
                        ),
                        "duration_ms": None,
                        "source": None,
                        "error": None,
                    }
                self.truncated = True

    def graph(
        self, *, script_path: str, status: str, error: Mapping[str, Any] | None = None
    ) -> ComputationGraph:
        roots = dict(self.roots)
        if not roots:
            dependency_ids = {
                dependency
                for node in self.nodes.values()
                for dependency in node["dependencies"]
            }
            candidates = [
                digest for digest in self.nodes if digest not in dependency_ids
            ]
            for index, digest in enumerate(sorted(candidates)):
                roots[f"expression-{index:06d}"] = digest
        nodes = []
        for digest in sorted(self.nodes):
            item = self.nodes[digest]
            expression = item["expression"]
            source = item["source"]
            nodes.append(
                ComputationNode(
                    node_id=digest,
                    digest=digest,
                    operation=expression.operation_id,
                    operation_version=expression.operation_version,
                    result_type=expression.result.type_id,
                    dependencies=item["dependencies"],
                    arguments=item["arguments"],
                    evaluation=item["evaluation"],
                    cache=item["cache"],
                    duration_ms=item["duration_ms"],
                    source_file=None if source is None else source[0],
                    source_line=None if source is None else source[1],
                    error=item["error"],
                )
            )
        return ComputationGraph(
            nodes=tuple(nodes),
            roots=tuple(
                ComputationRoot(root_id, node_id)
                for root_id, node_id in sorted(roots.items())
            ),
            script_path=str(Path(script_path).resolve()),
            execution_status=status,
            execution_error=_safe_error(error),
            truncated=self.truncated,
            node_limit=self.max_nodes,
        )


class TracingEvaluator(Evaluator):
    """Evaluator preserving public behavior while observing expression creation."""

    def __init__(self, *, graph_recorder: ComputationGraphRecorder, **kwargs: Any):
        self.graph_recorder = graph_recorder
        super().__init__(**kwargs)

    def expression(self, operation, *, result, args=(), kwargs=None, **options):
        stable_args = tuple(args)
        stable_kwargs = dict(kwargs or {})
        expression = super().expression(
            operation,
            result=result,
            args=stable_args,
            kwargs=stable_kwargs,
            **options,
        )
        self.graph_recorder.record_expression(expression, stable_args, stable_kwargs)
        return expression


def inspect_computation_graph(
    script_path,
    *,
    timeout=30,
    arguments=(),
    evaluation_mode="deferred",
    cache_enabled=None,
    max_nodes=DEFAULT_MAX_GRAPH_NODES,
    output=None,
) -> ComputationGraph:
    """Evaluate a model in isolation and return its typed computation graph."""
    from zencad.runtime.script_evaluator import (
        MissingSceneError,
        ScriptExecutionError,
        evaluate_static_script,
    )

    try:
        result = evaluate_static_script(
            script_path,
            timeout=timeout,
            arguments=arguments,
            evaluation_mode=evaluation_mode,
            cache_enabled=cache_enabled,
            output=output,
            capture_graph=True,
            graph_max_nodes=max_nodes,
        )
    except (MissingSceneError, ScriptExecutionError) as exception:
        if exception.graph is None:
            raise
        return ComputationGraph.from_dict(exception.graph)
    if result.graph is None:
        raise RuntimeError("Runner did not return a computation graph")
    return ComputationGraph.from_dict(result.graph)


__all__ = [
    "ComputationGraph",
    "ComputationNode",
    "ComputationRoot",
    "GraphArgument",
    "GRAPH_SCHEMA",
    "GRAPH_SCHEMA_VERSION",
    "inspect_computation_graph",
]
