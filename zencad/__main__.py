#!/usr/bin/env python3
# coding:utf-8

import argparse
import os
from pathlib import Path
import runpy
import signal
import sys
import tempfile
import threading

from zencad.gui.defaults import EVENT_LOOP_PULSE_MS, SCRIPT_TEMPLATE


TEMPLATE = SCRIPT_TEMPLATE


def console_options_handle(argv=None):
    parser = argparse.ArgumentParser(prog="zencad")
    parser.add_argument("--settings", action="store_true",
                        help="open the settings dialog")
    parser.add_argument("--display", action="store_true",
                        help="run a script in a standalone viewer")
    parser.add_argument("--no-show", action="store_true",
                        help="evaluate a script without creating a GUI")
    parser.add_argument("--no-restore", action="store_true",
                        help="start with the default window layout")
    parser.add_argument("--size", help=argparse.SUPPRESS)
    parser.add_argument("-m", help=argparse.SUPPRESS)
    parser.add_argument("paths", nargs="*", help="Python script to open")

    pargs = parser.parse_args(argv)
    return pargs


def frame_creator(openpath, norestore):
    from zencad.gui.mainwindow import MainWindow

    if openpath is None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False,
        ) as temporary:
            temporary.write(SCRIPT_TEMPLATE)
            openpath = temporary.name

    mainwindow = MainWindow(
        restore_gui=not norestore,
    )

    return mainwindow, openpath


def _run_script_path(path):
    script_path = Path(path).resolve()
    if not script_path.is_file():
        raise FileNotFoundError(script_path)
    os.chdir(script_path.parent)
    sys.path.insert(0, str(script_path.parent))
    runpy.run_path(str(script_path), run_name="__main__")


def _run_no_show(argv):
    paths = [argument for argument in argv if argument != "--no-show"]
    if len(paths) != 1:
        raise SystemExit("--no-show requires exactly one script")

    # Keep this path independent of the optional GUI stack.  In
    # particular, a headless wheel must be able to evaluate a model without
    # importing Qt merely to configure show().
    import zencad.showapi
    zencad.showapi.NOSHOW = True
    _run_script_path(paths[0])


def _run_script_only(pargs):
    if len(pargs.paths) != 1:
        raise SystemExit("--display/--no-show requires exactly one script")
    if pargs.no_show:
        import zencad.showapi

        zencad.showapi.NOSHOW = True
    _run_script_path(pargs.paths[0])


def _run_main_window(pargs):
    from PyQt5 import QtCore, QtWidgets

    application = QtWidgets.QApplication(sys.argv[1:])
    interrupted = []
    previous_sigint = None
    sigint_replaced = False
    if threading.current_thread() is threading.main_thread():
        previous_sigint = signal.getsignal(signal.SIGINT)
        if previous_sigint in (signal.SIG_DFL, signal.default_int_handler):
            def handle_sigint(signum, _frame):
                interrupted.append(signum)
                application.quit()

            signal.signal(signal.SIGINT, handle_sigint)
            sigint_replaced = True

    pulse = QtCore.QTimer(application)
    pulse.setInterval(EVENT_LOOP_PULSE_MS)
    pulse.timeout.connect(lambda: None)
    window = None
    try:
        openpath = pargs.paths[0] if pargs.paths else None
        window, openpath = frame_creator(openpath, pargs.no_restore)
        if openpath:
            window.open(openpath)
        window.show()
        pulse.start()
        exit_code = application.exec()
    finally:
        pulse.stop()
        if interrupted and window is not None:
            window.close()
        if sigint_replaced:
            signal.signal(signal.SIGINT, previous_sigint)

    if interrupted:
        return 128 + interrupted[-1]
    return exit_code


def main():
    argv = sys.argv[1:]
    if argv[:1] == ["check"]:
        from zencad.check import check_cli

        return check_cli(argv[1:])
    if argv[:1] == ["inspect"]:
        from zencad.inspect import inspect_cli

        return inspect_cli(argv[1:])
    if argv[:1] == ["render"]:
        from zencad.render import render_cli

        return render_cli(argv[1:])
    removed_modes = ("--unbound", "--frame", "--sleeped")
    if any(option in argv for option in removed_modes):
        raise SystemExit(
            "Foreign-window --unbound/--frame/--sleeped modes were removed; "
            "run 'zencad SCRIPT.py' or use --display for a standalone viewer"
        )
    if "--no-show" in argv:
        _run_no_show(argv)
        return 0

    # OCCT's Linux Xw_Window requires an X11 XID.  Select XWayland before
    # QApplication needs the backend choice before importing Qt on Wayland.
    from zencad.gui.qt_backend import configure_qt_platform
    configure_qt_platform()

    pargs = console_options_handle(argv)
    try:
        import PyQt5  # noqa: F401
    except ImportError as exception:
        raise SystemExit(
            "ZenCad GUI dependencies are missing; install them with "
            "'python -m pip install zencad[gui]'"
        ) from exception

    if pargs.settings:
        import zencad.gui.settingswdg
        zencad.gui.settingswdg.doit()
        return 0

    if pargs.display or pargs.no_show:
        _run_script_only(pargs)
        return 0
    return _run_main_window(pargs)


if __name__ == "__main__":
    raise SystemExit(main())
