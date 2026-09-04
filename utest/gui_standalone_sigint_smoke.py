#!/usr/bin/env python3
"""Verify that Ctrl+C escapes a standalone viewer's native Qt event loop."""

import os
from pathlib import Path
import signal
import subprocess
import sys


def run_viewer():
    from PyQt5 import QtCore
    from zencad import box, display, show

    display(box(1))

    def send_sigint(_widget, _thread):
        QtCore.QTimer.singleShot(
            500,
            lambda: os.kill(os.getpid(), signal.SIGINT),
        )

    show(animate=lambda _state: None, preanimate=send_sigint)


def main():
    if sys.argv[1:] == ["--viewer"]:
        run_viewer()
        return

    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--viewer"],
        timeout=15,
        check=False,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    assert completed.returncode == 128 + signal.SIGINT, (
        "standalone viewer returned {} after SIGINT instead of {}".format(
            completed.returncode,
            128 + signal.SIGINT,
        )
    )
    assert "glXMakeCurrent() has failed" not in completed.stderr, (
        "OCCT tried to use a destroyed GLX window during shutdown:\n{}".format(
            completed.stderr
        )
    )
    print("ZenCad standalone SIGINT smoke: OK")


if __name__ == "__main__":
    main()
