"""Shared non-GUI execution boundary for static ZenCad scripts."""

from dataclasses import dataclass
import math
from pathlib import Path
import threading
from typing import Callable, Mapping

from evalcache import EvaluationMode

from zencad.runtime.scene_protocol import SceneSnapshot


class StaticScriptError(RuntimeError):
    """Base class for managed static-script failures."""


class ScriptExecutionError(StaticScriptError):
    """The user script or its isolated runner failed."""

    def __init__(
        self,
        payload: Mapping[str, object],
        *,
        graph: Mapping[str, object] | None = None,
    ):
        self.payload = dict(payload)
        self.graph = None if graph is None else dict(graph)
        message = str(self.payload.get("message") or "script evaluation failed")
        exception_type = self.payload.get("exception_type")
        if exception_type:
            message = f"{exception_type}: {message}"
        traceback_text = str(self.payload.get("traceback") or "").rstrip()
        if traceback_text:
            message = f"{message}\n{traceback_text}"
        super().__init__(message)


class ScriptTimeoutError(StaticScriptError):
    """The user script exceeded the requested deadline."""

    def __init__(self, timeout: float):
        self.timeout = timeout
        super().__init__(f"Script did not finish within {timeout:g} seconds")


class AnimatedScriptError(StaticScriptError):
    """A live animation has no final static scene to inspect or render."""

    def __init__(self, message, *, graph=None):
        self.graph = None if graph is None else dict(graph)
        super().__init__(message)


class MissingSceneError(StaticScriptError):
    """The script completed without publishing a managed scene."""

    def __init__(self, message, *, graph=None):
        self.graph = None if graph is None else dict(graph)
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class StaticScriptResult:
    snapshot: SceneSnapshot
    output: tuple[tuple[str, str], ...]
    graph: Mapping[str, object] | None = None


def evaluate_static_script(
    script_path,
    *,
    arguments=(),
    timeout=30,
    evaluation_mode: EvaluationMode | str = EvaluationMode.DEFERRED,
    cache_enabled: bool | None = None,
    output: Callable[[str, str], None] | None = None,
    capture_graph: bool = False,
    graph_max_nodes: int = 4096,
) -> StaticScriptResult:
    """Run a script in isolation and return its last published static scene."""
    from zencad.runtime.runner_supervisor import RunnerSupervisor

    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)
    timeout = float(timeout)
    if timeout <= 0 or not math.isfinite(timeout):
        raise ValueError("Timeout must be a positive finite number")
    if not isinstance(arguments, (tuple, list)) or not all(
        isinstance(argument, str) for argument in arguments
    ):
        raise TypeError("Script arguments must be a sequence of strings")

    animated = threading.Event()
    captured_output = []
    supervisor = None

    def on_message(message):
        if message.message_type == "output":
            stream = message.payload["stream"]
            text = message.payload["text"]
            captured_output.append((stream, text))
            if output is not None:
                output(stream, text)
        elif message.message_type == "ready" and message.payload.get("animated"):
            animated.set()
            supervisor.cancel_current()

    supervisor = RunnerSupervisor(
        on_message=on_message,
        evaluation_mode=evaluation_mode,
        cache_enabled=cache_enabled,
        capture_graph=capture_graph,
        graph_max_nodes=graph_max_nodes,
    )
    try:
        generation = supervisor.start(script, arguments=list(arguments))
        try:
            status = supervisor.wait(generation, timeout=timeout)
        except TimeoutError as exception:
            supervisor.cancel_current(grace_period=0.2)
            try:
                supervisor.wait(generation, timeout=2)
            except TimeoutError:
                pass
            raise ScriptTimeoutError(timeout) from exception

        messages = tuple(
            message
            for message in supervisor.messages
            if message.generation == generation
        )
        graphs = [
            message.payload.get("graph")
            for message in messages
            if message.message_type == "graph"
        ]
        graph = graphs[-1] if graphs else None
        if animated.is_set():
            raise AnimatedScriptError(
                "Animated show() sessions do not have a final static scene",
                graph=graph,
            )
        errors = [message for message in messages if message.message_type == "error"]
        if errors:
            raise ScriptExecutionError(errors[-1].payload, graph=graph)
        if status != "success":
            raise ScriptExecutionError(
                {
                    "kind": "runner",
                    "exception_type": "RunnerError",
                    "message": f"Script runner finished with status {status!r}",
                    "traceback": "",
                },
                graph=graph,
            )

        scenes = [message.snapshot for message in messages if message.snapshot]
        if not scenes:
            raise MissingSceneError(
                "Script did not call show() with a scene",
                graph=graph,
            )
        return StaticScriptResult(scenes[-1], tuple(captured_output), graph)
    finally:
        if supervisor is not None:
            supervisor.shutdown()


__all__ = [
    "AnimatedScriptError",
    "MissingSceneError",
    "ScriptExecutionError",
    "ScriptTimeoutError",
    "StaticScriptError",
    "StaticScriptResult",
    "evaluate_static_script",
]
