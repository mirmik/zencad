"""Spawn-safe entry point for one isolated ZenCad script generation."""

import os
from pathlib import Path
import runpy
import sys
import traceback
from uuid import uuid4

from zencad.runtime.input_protocol import (
    InputEventBuffer,
    decode_input_frame,
)
from zencad.runtime.runner_protocol import (
    decode_control_message,
    encode_control_message,
)
from zencad.runtime.scene_protocol import (
    FileSnapshotBundle,
    encode_snapshot_frame,
    select_snapshot_transport,
)
from zencad.runtime.scene_patch_protocol import encode_scene_patch_frame
from zencad.scene_draft import SceneAnimationCancelled


class RunnerCancelled(BaseException):
    pass


class _Reporter:
    def __init__(self, connection, generation):
        self.connection = connection
        self.generation = generation
        self.closed = False

    def control(self, message_type, **payload):
        if self.closed:
            return False
        try:
            self.connection.send_bytes(
                encode_control_message(
                    message_type,
                    self.generation,
                    **payload,
                )
            )
        except (BrokenPipeError, EOFError, OSError):
            self.closed = True
            return False
        return True

    def scene(self, snapshot, bundle_root):
        if select_snapshot_transport(snapshot) == "inline":
            self.connection.send_bytes(encode_snapshot_frame(snapshot))
            return
        name = f"generation-{self.generation}-{uuid4().hex}"
        FileSnapshotBundle.write(Path(bundle_root) / name, snapshot)
        self.control("scene_file", bundle=name)

    def scene_patch(self, patch):
        if self.closed:
            return False
        try:
            self.connection.send_bytes(encode_scene_patch_frame(patch))
        except (BrokenPipeError, EOFError, OSError):
            self.closed = True
            return False
        return True


class _OutputStream:
    encoding = "utf-8"

    def __init__(self, reporter, stream):
        self.reporter = reporter
        self.stream = stream

    def write(self, text):
        if text:
            text = str(text)
            for offset in range(0, len(text), 64 * 1024):
                self.reporter.control(
                    "output",
                    stream=self.stream,
                    text=text[offset:offset + 64 * 1024],
                )
        return len(text)

    def flush(self):
        return None

    def isatty(self):
        return False


class _EvalCacheCommunicator:
    def __init__(self, reporter):
        self.reporter = reporter

    def send(self, data):
        if data.get("cmd") != "evalcache":
            return
        payload = {key: value for key, value in data.items() if key != "cmd"}
        self.reporter.control("progress", **payload)


def _cancel_trace(cancel_event):
    def trace(frame, event, argument):
        if cancel_event.is_set():
            raise RunnerCancelled()
        return trace

    return trace


class _InputReceiver:
    """Drain and validate one generation's reverse input pipe."""

    def __init__(self, connection, generation):
        self.connection = connection
        self.generation = generation
        self.buffer = InputEventBuffer(generation)

    def drain(self):
        trace = sys.gettrace()
        if trace is not None:
            sys.settrace(None)
        try:
            received = 0
            while received < 4096 and self.connection.poll():
                event = decode_input_frame(self.connection.recv_bytes())
                self.buffer.push(event)
                received += 1
            return self.buffer.drain()
        except (EOFError, OSError):
            return self.buffer.drain()
        finally:
            if trace is not None:
                sys.settrace(trace)


def run_generation(
    request_frame,
    connection,
    input_connection,
    cancel_event,
    bundle_root,
):
    """Evaluate one run request and emit framed generation messages."""
    reporter = None
    generation = 0
    terminal_status = "error"
    try:
        message_type, generation, request = decode_control_message(request_frame)
        if message_type != "run":
            raise ValueError("Runner worker requires a run request")
        reporter = _Reporter(connection, generation)
        input_receiver = _InputReceiver(input_connection, generation)
        script_path = Path(request["script_path"]).resolve()
        cwd = Path(request.get("cwd") or script_path.parent).resolve()
        arguments = request.get("arguments", [])
        if not isinstance(arguments, list) or not all(
            isinstance(item, str) for item in arguments
        ):
            raise ValueError("Runner arguments must be a list of strings")
        if not script_path.is_file():
            raise FileNotFoundError(script_path)
        if not cwd.is_dir():
            raise NotADirectoryError(cwd)

        import zencad
        from zencad.lazifier import install_evalcahe_notication
        from zencad.showapi import managed_scene

        cache_directory = request.get("cache_directory")
        cache_enabled = request.get("cache_enabled", True)
        if cache_directory is None:
            zencad.configure(cache_enabled=cache_enabled)
        else:
            zencad.configure(
                cache_dir=cache_directory,
                cache_enabled=cache_enabled,
            )

        install_evalcahe_notication(_EvalCacheCommunicator(reporter))
        reporter.control("started", pid=os.getpid(), cwd=str(cwd))
        reporter.control("progress", subcmd="runner", phase="evaluating")

        previous_cwd = Path.cwd()
        previous_argv = sys.argv
        previous_path = list(sys.path)
        try:
            os.chdir(cwd)
            sys.argv = [str(script_path), *arguments]
            sys.path.insert(0, str(script_path.parent))
            sys.stdout = _OutputStream(reporter, "stdout")
            sys.stderr = _OutputStream(reporter, "stderr")
            sys.settrace(_cancel_trace(cancel_event))
            with managed_scene(
                generation,
                lambda snapshot: reporter.scene(snapshot, bundle_root),
                patch_publisher=reporter.scene_patch,
                ready_publisher=lambda revision, animated: reporter.control(
                    "ready",
                    scene_revision=revision,
                    animated=animated,
                ),
                cancel_event=cancel_event,
                input_drain=input_receiver.drain,
            ):
                runpy.run_path(str(script_path), run_name="__main__")
            terminal_status = "success"
        finally:
            sys.settrace(None)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.argv = previous_argv
            sys.path[:] = previous_path
            os.chdir(previous_cwd)
    except (RunnerCancelled, SceneAnimationCancelled):
        terminal_status = "cancelled"
    except SystemExit as exception:
        if exception.code in (None, 0):
            terminal_status = "success"
        elif reporter is not None:
            reporter.control(
                "error",
                kind="system_exit",
                exception_type="SystemExit",
                message=str(exception.code),
                traceback=traceback.format_exc(),
            )
    except BaseException as exception:
        if reporter is None:
            reporter = _Reporter(connection, generation)
        reporter.control(
            "error",
            kind="exception",
            exception_type=type(exception).__name__,
            message=str(exception),
            traceback=traceback.format_exc(),
        )
    finally:
        if reporter is not None:
            reporter.control("finished", status=terminal_status)
        try:
            connection.close()
        except OSError:
            pass
        try:
            input_connection.close()
        except OSError:
            pass
