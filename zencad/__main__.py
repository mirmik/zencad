#!/usr/bin/env python3
# coding:utf-8

import os
from pathlib import Path
import runpy
import sys

TEMPLATE = """#!/usr/bin/env python3
# coding: utf-8

from zencad import *

model = box(10)
display(model)
show()
"""


def console_options_handle():
    import zenframe.argparse
    parser = zenframe.argparse.ArgumentParser()

    # Смотри аргументы в zenframe.ArgumentParser
    parser.add_argument("--settings", action="store_true",
                        help="Execute settings utility")

    pargs = parser.parse_args()
    return pargs


def frame_creator(openpath, norestore):
    from zencad.gui.mainwindow import MainWindow
    from zenframe.util import create_temporary_file
    import zenframe.configuration

    if openpath is None:
        openpath = create_temporary_file(
            zenframe.configuration.Configuration.TEMPLATE)

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

    # Keep this path independent of the optional GUI/ZenFrame stack.  In
    # particular, a headless wheel must be able to evaluate a model without
    # importing Qt merely to configure show().
    import zencad.showapi
    zencad.showapi.NOSHOW = True
    _run_script_path(paths[0])


def _run_script_only(pargs):
    import zenframe.configuration

    if len(pargs.paths) != 1:
        raise SystemExit("--display/--no-show requires exactly one script")
    zenframe.configuration.Configuration.NOSHOW = bool(pargs.no_show)
    zenframe.configuration.Configuration.WIDGET_ONLY = bool(pargs.display)
    _run_script_path(pargs.paths[0])


def _run_main_window(pargs):
    from PyQt5 import QtCore, QtWidgets
    import zenframe.configuration

    application = QtWidgets.QApplication(sys.argv[1:])
    openpath = pargs.paths[0] if pargs.paths else None
    window, openpath = frame_creator(openpath, pargs.no_restore)
    if openpath:
        window.open(openpath)
    pulse = QtCore.QTimer()
    pulse.start(int(zenframe.configuration.Configuration.TIMER_PULSE * 1000))
    pulse.timeout.connect(lambda: None)
    window.show()
    return application.exec()


def main():
    argv = sys.argv[1:]
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
    # zenframe creates QApplication when ZenCad is launched from Wayland.
    from zencad.gui.qt_backend import configure_qt_platform
    configure_qt_platform()

    try:
        import zenframe.configuration
        pargs = console_options_handle()
    except ImportError as exception:
        raise SystemExit(
            "ZenCad GUI dependencies are missing; install them with "
            "'python -m pip install zencad[gui]'"
        ) from exception

    zenframe.configuration.Configuration.TEMPLATE = TEMPLATE

    if pargs.settings:
        import zencad.gui.settingswdg
        zencad.gui.settingswdg.doit()
        sys.exit()

    if pargs.display or pargs.no_show:
        _run_script_only(pargs)
        return 0
    return _run_main_window(pargs)


if __name__ == "__main__":
    main()
