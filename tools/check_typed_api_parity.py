#!/usr/bin/env python3
"""Validate and render the legacy-to-typed geometry API parity matrix."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "development" / "typed-api-parity.json"
ALLOWED_STATUSES = {
    "implemented",
    "partial",
    "missing",
    "repair",
    "unchanged",
}


class ContractError(RuntimeError):
    pass


def _load_matrix() -> dict[str, Any]:
    with MATRIX_PATH.open(encoding="utf-8") as stream:
        matrix = json.load(stream)
    if matrix.get("schema_version") != 1:
        raise ContractError("unsupported parity matrix schema")
    return matrix


def _module_tree(module_name: str) -> tuple[Path, ast.Module]:
    module = importlib.import_module(module_name)
    module_file = getattr(module, "__file__", None)
    if not module_file:
        raise ContractError(f"{module_name} has no Python source file")
    path = Path(module_file)
    return path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _top_level_definitions(tree: ast.Module) -> dict[str, ast.AST]:
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            definitions[node.target.id] = node
    return definitions


def _class_methods(node: ast.ClassDef) -> dict[str, ast.AST]:
    return {
        child.name: child
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _signature(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return f"({ast.unparse(node.args)})"
    if isinstance(node, ast.ClassDef):
        constructor = _class_methods(node).get("__init__")
        if constructor is None:
            constructor = _class_methods(node).get("__new__")
        if constructor is None:
            return "<type>"
        return _signature(constructor)
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        return "<value>"
    raise ContractError(f"cannot obtain a signature for {type(node).__name__}")


def _selected_members(surface: dict[str, Any]) -> dict[str, ast.AST]:
    module_name, separator, class_name = surface["source"].partition(":")
    _, tree = _module_tree(module_name)
    definitions = _top_level_definitions(tree)
    if separator:
        class_node = definitions.get(class_name)
        if not isinstance(class_node, ast.ClassDef):
            raise ContractError(f"{surface['source']} is not a source class")
        candidates = _class_methods(class_node)
        public = {
            name: node for name, node in candidates.items() if not name.startswith("_")
        }
        for name in surface.get("dunder", []):
            if name not in candidates:
                raise ContractError(f"{surface['source']} has no method {name}")
            public[name] = candidates[name]
        if surface.get("include_type", False):
            public["@type"] = class_node
    else:
        public = {
            name: node for name, node in definitions.items() if not name.startswith("_")
        }

    exclusions = surface.get("exclude", {})
    unknown_exclusions = set(exclusions) - set(public)
    if unknown_exclusions:
        raise ContractError(
            f"{surface['source']} has stale exclusions: {sorted(unknown_exclusions)}"
        )
    return {name: node for name, node in public.items() if name not in exclusions}


def _canonical_name(surface: dict[str, Any], member: str) -> str:
    module_name, separator, class_name = surface["source"].partition(":")
    if not separator:
        return f"{module_name}:{member}"
    if member == "@type":
        return f"{module_name}:{class_name}"
    return f"{module_name}:{class_name}.{member}"


def _format_target(template: str, member: str) -> str:
    visible_name = member if member != "@type" else "type"
    return template.format(name=visible_name)


def expand(matrix: dict[str, Any]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for family in matrix["families"]:
        checks = family.get("checks", [])
        if not checks:
            raise ContractError(f"family {family['id']} has no characterization checks")
        for check in checks:
            if not (ROOT / check).exists():
                raise ContractError(
                    f"family {family['id']} check does not exist: {check}"
                )
        for surface in family["surfaces"]:
            default = surface["default"]
            overrides = surface.get("overrides", {})
            selected = _selected_members(surface)
            stale_overrides = set(overrides) - set(selected)
            if stale_overrides:
                raise ContractError(
                    f"{surface['source']} has stale overrides: {sorted(stale_overrides)}"
                )
            for member, node in selected.items():
                policy = {**default, **overrides.get(member, {})}
                status = policy["status"]
                if status not in ALLOWED_STATUSES:
                    raise ContractError(
                        f"{surface['source']}:{member} has invalid status {status}"
                    )
                target = _format_target(policy["typed"], member)
                if not target.strip():
                    raise ContractError(f"{surface['source']}:{member} has no target")
                canonical = _canonical_name(surface, member)
                if canonical in seen:
                    raise ContractError(f"duplicate matrix entry: {canonical}")
                seen.add(canonical)
                entries.append(
                    {
                        "family": family["id"],
                        "legacy": canonical,
                        "member": member,
                        "signature": _signature(node),
                        "status": status,
                        "typed": target,
                        "materialization": policy.get(
                            "materialization", default.get("materialization", "none")
                        ),
                    }
                )
    return entries


def signature_digest(entries: list[dict[str, str]]) -> str:
    payload = "\n".join(
        f"{entry['legacy']} {entry['signature']}"
        for entry in sorted(entries, key=lambda row: row["legacy"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate(matrix: dict[str, Any], entries: list[dict[str, str]]) -> None:
    digest = signature_digest(entries)
    expected = matrix.get("legacy_signature_sha256")
    if digest != expected:
        raise ContractError(
            "legacy API signature snapshot changed: "
            f"expected {expected!r}, actual {digest!r}"
        )
    if not entries:
        raise ContractError("parity matrix is empty")
    if not any(entry["status"] == "missing" for entry in entries):
        raise ContractError(
            "matrix no longer contains missing work; reconcile the board"
        )
    root_exports = matrix.get("root_exports", [])
    if len(root_exports) != len(set(root_exports)):
        raise ContractError("root export contract contains duplicate names")
    zencad = importlib.import_module("zencad")
    missing_exports = [name for name in root_exports if not hasattr(zencad, name)]
    if missing_exports:
        raise ContractError(
            f"intentional zencad root exports disappeared: {missing_exports}"
        )


def _render(entries: list[dict[str, str]]) -> str:
    lines = [
        "| Family | Legacy symbol | Signature | Status | Typed contract | Materialization |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in sorted(entries, key=lambda row: (row["family"], row["legacy"])):
        cells = [
            entry["family"],
            f"`{entry['legacy']}`",
            f"`{entry['signature']}`",
            entry["status"],
            f"`{entry['typed']}`",
            entry["materialization"],
        ]
        lines.append(
            "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--render", action="store_true", help="print the expanded Markdown matrix"
    )
    parser.add_argument(
        "--digest", action="store_true", help="print the current signature digest"
    )
    args = parser.parse_args()
    try:
        matrix = _load_matrix()
        entries = expand(matrix)
        if args.digest:
            print(signature_digest(entries))
            return 0
        validate(matrix, entries)
    except (ContractError, KeyError, TypeError, json.JSONDecodeError) as exception:
        print(f"typed API parity check failed: {exception}", file=sys.stderr)
        return 1

    counts = Counter(entry["status"] for entry in entries)
    print(
        f"typed API parity: {len(entries)} symbols; "
        + ", ".join(f"{name}={counts[name]}" for name in sorted(counts))
    )
    if args.render:
        print()
        print(_render(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
