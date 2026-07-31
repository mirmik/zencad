"""Generation-filtered lifecycle manager for isolated ZenCad runners."""

from dataclasses import dataclass, field
import multiprocessing
from pathlib import Path
import shutil
import tempfile
import threading
from typing import Callable

from zencad.runtime.runner_protocol import (
    RUNNER_MAGIC,
    RunnerMessage,
    decode_control_message,
    encode_control_message,
)
from zencad.runtime.scene_protocol import (
    FRAME_MAGIC,
    FileSnapshotBundle,
    ProtocolError,
    decode_snapshot_frame,
)


@dataclass
class _RunnerHandle:
    generation: int
    process: multiprocessing.Process
    connection: object
    cancel_event: object
    data_root: Path
    finished: threading.Event = field(default_factory=threading.Event)
    cancel_requested: bool = False
    hard_cancelled: bool = False
    saw_finished: bool = False
    status: str | None = None


class RunnerSupervisor:
    """Start disposable runners without allowing stale generations to commit."""

    def __init__(
        self,
        on_message: Callable[[RunnerMessage], None] | None = None,
        cancel_grace_period: float = 0.5,
    ):
        if cancel_grace_period < 0:
            raise ValueError("Cancellation grace period must be non-negative")
        self.on_message = on_message
        self.cancel_grace_period = cancel_grace_period
        self._context = multiprocessing.get_context("spawn")
        self._lock = threading.RLock()
        self._generation = 0
        self._current_generation: int | None = None
        self._handles: dict[int, _RunnerHandle] = {}
        self.messages: list[RunnerMessage] = []
        self.callback_errors: list[BaseException] = []

    @property
    def current_generation(self):
        with self._lock:
            return self._current_generation

    def start(self, script_path, arguments=None, cwd=None) -> int:
        from zencad.runtime.runner_worker import run_generation

        script_path = Path(script_path).resolve()
        if cwd is None:
            cwd = script_path.parent
        cwd = Path(cwd).resolve()
        if not script_path.is_file():
            raise FileNotFoundError(script_path)
        if not cwd.is_dir():
            raise NotADirectoryError(cwd)
        if arguments is None:
            arguments = []
        if not isinstance(arguments, (list, tuple)) or not all(
            isinstance(item, str) for item in arguments
        ):
            raise TypeError("Runner arguments must be a sequence of strings")
        arguments = list(arguments)

        with self._lock:
            previous = self._handles.get(self._current_generation)
            self._generation += 1
            generation = self._generation
            self._current_generation = generation
        if previous is not None and previous.process.is_alive():
            self._request_cancel(previous, self.cancel_grace_period)

        data_root = Path(tempfile.mkdtemp(prefix=f"zencad-run-{generation}-"))
        receive_connection, send_connection = self._context.Pipe(duplex=False)
        cancel_event = self._context.Event()
        request = encode_control_message(
            "run",
            generation,
            script_path=str(script_path),
            cwd=str(cwd),
            arguments=arguments,
            cache_directory=str(data_root / "cache"),
        )
        process = self._context.Process(
            target=run_generation,
            args=(request, send_connection, cancel_event, str(data_root)),
            name=f"zencad-runner-{generation}",
        )
        handle = _RunnerHandle(
            generation=generation,
            process=process,
            connection=receive_connection,
            cancel_event=cancel_event,
            data_root=data_root,
        )
        with self._lock:
            self._handles[generation] = handle
        process.start()
        send_connection.close()
        self._dispatch(RunnerMessage(
            "run",
            generation,
            {
                "script_path": str(script_path),
                "cwd": str(cwd),
                "arguments": arguments,
            },
        ))
        threading.Thread(
            target=self._read_messages,
            args=(handle,),
            name=f"zencad-runner-reader-{generation}",
            daemon=True,
        ).start()
        return generation

    def _dispatch(self, message: RunnerMessage):
        with self._lock:
            if message.generation != self._current_generation:
                return False
            self.messages.append(message)
        if self.on_message is not None:
            try:
                self.on_message(message)
            except BaseException as exception:
                self.callback_errors.append(exception)
        return True

    def _bundle_path(self, handle, name):
        if not isinstance(name, str) or Path(name).name != name:
            raise ProtocolError("Invalid runner bundle name")
        path = (handle.data_root / name).resolve()
        if path.parent != handle.data_root.resolve():
            raise ProtocolError("Runner bundle escaped its data directory")
        return path

    def _decode_message(self, handle, frame):
        if frame.startswith(FRAME_MAGIC):
            snapshot = decode_snapshot_frame(frame)
            if snapshot.generation != handle.generation:
                raise ProtocolError("Scene generation does not match its runner")
            return RunnerMessage(
                "scene",
                handle.generation,
                {"carrier": "inline"},
                snapshot=snapshot,
            )
        if not frame.startswith(RUNNER_MAGIC):
            raise ProtocolError("Unknown runner frame magic")
        message_type, generation, payload = decode_control_message(frame)
        if generation != handle.generation:
            raise ProtocolError("Control generation does not match its runner")
        if message_type == "scene_file":
            snapshot = FileSnapshotBundle.read(
                self._bundle_path(handle, payload.get("bundle"))
            )
            if snapshot.generation != handle.generation:
                raise ProtocolError("Scene bundle generation mismatch")
            return RunnerMessage(
                "scene",
                generation,
                {"carrier": "file"},
                snapshot=snapshot,
            )
        return RunnerMessage(message_type, generation, payload)

    def _read_messages(self, handle):
        protocol_failure = None
        try:
            while True:
                try:
                    frame = handle.connection.recv_bytes()
                except (EOFError, OSError):
                    break
                try:
                    message = self._decode_message(handle, frame)
                except Exception as exception:
                    protocol_failure = exception
                    handle.cancel_event.set()
                    if handle.process.is_alive():
                        handle.process.terminate()
                    break
                if message.message_type == "finished":
                    handle.saw_finished = True
                    handle.status = message.payload.get("status")
                self._dispatch(message)
                if message.message_type == "finished":
                    # `finished` is the terminal protocol frame.  Waiting for
                    # pipe EOF after it can block forever on Windows when a
                    # process was cooperatively cancelled.
                    break
        finally:
            try:
                handle.connection.close()
            except OSError:
                pass
            handle.process.join(timeout=1)
            if handle.process.is_alive():
                handle.process.terminate()
                handle.process.join(timeout=1)

            if protocol_failure is not None:
                handle.status = "protocol_error"
                self._dispatch(RunnerMessage(
                    "error",
                    handle.generation,
                    {
                        "kind": "protocol",
                        "exception_type": type(protocol_failure).__name__,
                        "message": str(protocol_failure),
                        "traceback": "",
                    },
                ))
            if not handle.saw_finished:
                if protocol_failure is not None:
                    status = "protocol_error"
                elif handle.cancel_requested:
                    status = "cancelled"
                else:
                    status = "crashed"
                    self._dispatch(RunnerMessage(
                        "error",
                        handle.generation,
                        {
                            "kind": "crash",
                            "exception_type": "RunnerCrash",
                            "message": (
                                f"Runner exited with code {handle.process.exitcode}"
                            ),
                            "traceback": "",
                        },
                    ))
                handle.status = status
                self._dispatch(RunnerMessage(
                    "finished",
                    handle.generation,
                    {"status": status, "hard": handle.hard_cancelled},
                ))
            shutil.rmtree(handle.data_root, ignore_errors=True)
            handle.finished.set()

    def _request_cancel(self, handle, grace_period):
        if grace_period < 0:
            raise ValueError("Cancellation grace period must be non-negative")
        if handle.cancel_requested:
            return
        handle.cancel_requested = True
        handle.cancel_event.set()

        def reap():
            handle.process.join(timeout=grace_period)
            if handle.process.is_alive():
                handle.hard_cancelled = True
                handle.process.terminate()
                handle.process.join(timeout=1)
                if handle.process.is_alive() and hasattr(handle.process, "kill"):
                    handle.process.kill()
                    handle.process.join(timeout=1)
                try:
                    # Closing the receiving endpoint wakes a Windows reader
                    # blocked in recv_bytes after forced termination.
                    handle.connection.close()
                except OSError:
                    pass

        threading.Thread(
            target=reap,
            name=f"zencad-runner-reaper-{handle.generation}",
            daemon=True,
        ).start()

    def cancel_current(self, grace_period=None):
        if grace_period is None:
            grace_period = self.cancel_grace_period
        with self._lock:
            handle = self._handles.get(self._current_generation)
        if handle is None or not handle.process.is_alive():
            return False
        self._request_cancel(handle, grace_period)
        return True

    def wait(self, generation=None, timeout=None):
        if generation is None:
            generation = self.current_generation
        with self._lock:
            handle = self._handles.get(generation)
        if handle is None:
            raise KeyError(generation)
        if not handle.finished.wait(timeout):
            raise TimeoutError(f"Runner generation {generation} is still active")
        return handle.status

    def is_alive(self, generation=None):
        if generation is None:
            generation = self.current_generation
        with self._lock:
            handle = self._handles.get(generation)
        return bool(handle and handle.process.is_alive())

    def shutdown(self, timeout=2):
        with self._lock:
            handles = list(self._handles.values())
        for handle in handles:
            if handle.process.is_alive():
                self._request_cancel(handle, 0)
        for handle in handles:
            handle.finished.wait(timeout)
