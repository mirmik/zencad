#!/usr/bin/env python3
"""Evaluate every bundled example and report all failures in one run."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time


ROOT = Path(__file__).parents[1]
EXAMPLES_ROOT = ROOT / "zencad" / "examples"


def example_paths(fast=False):
    paths = sorted(EXAMPLES_ROOT.rglob("*.py"))
    if fast or "TRAVIS_OS_NAME" in os.environ:
        paths = [path for path in paths if "Integration" not in path.parts]
        paths = [
            path for path in paths
            if path.relative_to(EXAMPLES_ROOT).as_posix() != "Models/logo.py"
        ]
    return paths


def _messages(supervisor, generation, message_type=None):
    return [
        message
        for message in supervisor.messages
        if message.generation == generation
        and (message_type is None or message.message_type == message_type)
    ]


def run_managed_example(supervisor, path, timeout):
    generation = supervisor.start(path)
    deadline = time.monotonic() + timeout
    ready = None
    while time.monotonic() < deadline:
        errors = _messages(supervisor, generation, "error")
        if errors:
            supervisor.wait(generation, timeout=5)
            return False, errors[-1].payload.get("traceback", "runner error")

        ready_messages = _messages(supervisor, generation, "ready")
        if ready_messages:
            ready = ready_messages[-1]
            break

        finished = _messages(supervisor, generation, "finished")
        if finished:
            status = finished[-1].payload.get("status")
            return False, f"runner finished as {status!r} before publishing a scene"
        time.sleep(0.01)

    if ready is None:
        supervisor.cancel_current()
        supervisor.wait(generation, timeout=5)
        return False, "timeout waiting for the initial scene"

    if not ready.payload.get("animated"):
        status = supervisor.wait(generation, timeout=max(1, timeout))
        return status == "success", f"static runner finished as {status!r}"

    while time.monotonic() < deadline:
        errors = _messages(supervisor, generation, "error")
        if errors:
            supervisor.wait(generation, timeout=5)
            return False, errors[-1].payload.get("traceback", "animation error")
        if _messages(supervisor, generation, "scene_patch"):
            supervisor.cancel_current()
            status = supervisor.wait(generation, timeout=5)
            return status == "cancelled", f"animation cancelled as {status!r}"
        time.sleep(0.01)

    supervisor.cancel_current()
    supervisor.wait(generation, timeout=5)
    return False, "animation produced no live scene patch"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--managed", action="store_true")
    parser.add_argument("--timeout", type=float, default=120)
    arguments = parser.parse_args(argv)

    paths = example_paths(arguments.fast)
    failures = []
    if arguments.managed:
        from zencad.runtime.runner_supervisor import RunnerSupervisor

        with TemporaryDirectory() as cache_directory:
            supervisor = RunnerSupervisor(cache_directory=cache_directory)
            try:
                for index, path in enumerate(paths, 1):
                    relative = path.relative_to(EXAMPLES_ROOT)
                    print(f"[{index:02d}/{len(paths):02d}] {relative}", flush=True)
                    success, details = run_managed_example(
                        supervisor, path, arguments.timeout
                    )
                    if success:
                        print("  OK", flush=True)
                    else:
                        failures.append((relative, "managed", "", details))
                        print("  FAIL", flush=True)
            finally:
                supervisor.shutdown()
    else:
        for index, path in enumerate(paths, 1):
            relative = path.relative_to(EXAMPLES_ROOT)
            print(f"[{index:02d}/{len(paths):02d}] {relative}", flush=True)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "zencad", "--no-show", str(path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    timeout=arguments.timeout,
                )
            except subprocess.TimeoutExpired as exception:
                failures.append(
                    (relative, "timeout", exception.stdout, exception.stderr)
                )
                print("  TIMEOUT", flush=True)
                continue
            if result.returncode:
                failures.append(
                    (
                        relative,
                        f"exit {result.returncode}",
                        result.stdout,
                        result.stderr,
                    )
                )
                print(f"  FAIL ({result.returncode})", flush=True)
            else:
                print("  OK", flush=True)

    if failures:
        print("\nExample failures:")
        for relative, reason, stdout, stderr in failures:
            print(f"\n--- {relative} ({reason}) ---")
            if stdout:
                print(stdout.rstrip())
            if stderr:
                print(stderr.rstrip())
        return 1

    print(f"\nAll {len(paths)} examples evaluated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
