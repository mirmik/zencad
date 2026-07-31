#!/usr/bin/env python3
# coding:utf-8

import os
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


def top_half(communicator):
    from zencad.lazifier import install_evalcahe_notication
    install_evalcahe_notication(communicator)


def frame_creator(openpath, initial_communicator, norestore, unbound):
    from zencad.gui.mainwindow import MainWindow
    from zencad.settings import Settings
    from zenframe.util import create_temporary_file
    import zenframe.configuration
    import PyQt5.QtWidgets
    import PyQt5.QtGui

    iconpath = os.path.join(os.path.dirname(__file__), "industrial-robot.svg")
    if not os.path.exists(iconpath):
        # for pyinstaller files configuration
        iconpath = os.path.join(os.path.dirname(
            __file__), "zencad", "industrial-robot.svg")

    PyQt5.QtWidgets.QApplication.instance().setWindowIcon(PyQt5.QtGui.QIcon())

    if openpath is None and not unbound:
        openpath = create_temporary_file(
            zenframe.configuration.Configuration.TEMPLATE)

    mainwindow = MainWindow(
        initial_communicator=initial_communicator,
        restore_gui=not norestore,
        managed_runtime=not unbound)

    return mainwindow, openpath


def main():
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

    from zencad.showapi import widget_creator
    import zenframe.starter as frame

    frame.invoke(
        pargs,
        frame_creator=frame_creator,
        exec_top_half=top_half,
        exec_bottom_half=widget_creator)


if __name__ == "__main__":
    main()
