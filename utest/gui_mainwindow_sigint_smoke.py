#!/usr/bin/env python3
"""Verify that the no-argument ZenCad application opens and handles Ctrl+C."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "zencad", "--no-restore"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(2)
        assert process.poll() is None, "ZenCad exited before Ctrl+C"
        os.kill(process.pid, signal.SIGINT)
        stdout, stderr = process.communicate(timeout=15)
    except Exception:
        process.kill()
        process.wait()
        raise

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    assert process.returncode == 128 + signal.SIGINT, (
        "ZenCad returned {} after SIGINT instead of {}".format(
            process.returncode,
            128 + signal.SIGINT,
        )
    )
    assert "glXMakeCurrent() has failed" not in stderr, (
        "OCCT used a destroyed GLX window during shutdown:\n{}".format(stderr)
    )
    print("ZenCad main-window SIGINT smoke: OK")


if __name__ == "__main__":
    main()
