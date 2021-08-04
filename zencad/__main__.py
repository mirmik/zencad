#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import time

import psutil
import traceback
import runpy
import signal

import zenframe.argparse
import zenframe.configuration

zenframe.configuration.Configuration.TEMPLATE = """#!/usr/bin/env python3
#coding: utf-8

from zencad import *

m=box(10)
disp(m)

show()"""


def console_options_handle():

    parser = zenframe.argparse.ArgumentParser()

    # Смотри аргументы в zenframe.ArgumentParser
    parser.add_argument("--installer", action="store_true",
                        help="Execute installer utility")
    parser.add_argument("--settings", action="store_true",
                        help="Execute settings utility")
    parser.add_argument("--install-libs", action="store_true",
                        help="Console dialog for install third-libraries")
    parser.add_argument("--install-occt-force", nargs="*",
                        default=None, help="Download and install libocct")
    parser.add_argument("--install-occt-to-pythonocc-dir", action="store_true",
                        default=None, help="Download and install libocct")
    parser.add_argument("--install-pythonocc-force", action="store_true",
                        help="Download and install pythonocc package")
    parser.add_argument("--lookup-libraries", action="store_true",
                        help="Lookup depends")
    parser.add_argument("--yes", action="store_true")

    pargs = parser.parse_args()
    return pargs


def top_half(communicator):
    from zencad.lazifier import install_evalcahe_notication
    install_evalcahe_notication(communicator)


def frame_creator(openpath, initial_communicator, norestore, unbound):
    from zencad.gui.mainwindow import MainWindow
    from zencad.settings import Settings
    from zenframe.util import create_temporary_file
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
        restore_gui=not norestore)

    return mainwindow, openpath


def main():
    pargs = console_options_handle()

    if pargs.settings:
        import zencad.gui.settingswdg
        zencad.gui.settingswdg.doit()
        sys.exit()

    if pargs.installer:
        import zencad.gui.libinstaller
        zencad.gui.libinstaller.doit()
        sys.exit()

    if pargs.install_libs:
        from zencad.geometry_core_installer import console_third_libraries_installer_utility
        console_third_libraries_installer_utility(yes=pargs.yes)
        sys.exit()

    if pargs.install_pythonocc_force:
        from zencad.geometry_core_installer import install_precompiled_python_occ
        install_precompiled_python_occ()
        return

    if pargs.lookup_libraries:
        from zencad.geometry_core_installer import test_third_libraries
        print(test_third_libraries())
        return

    if pargs.install_occt_force is not None:
        from zencad.geometry_core_installer import install_precompiled_occt_library
        path = pargs.install_occt_force[0] if len(
            pargs.install_occt_force) > 0 else None
        install_precompiled_occt_library(tgtpath=path)
        return

    if pargs.install_occt_to_pythonocc_dir:
        from zencad.geometry_core_installer import install_precompiled_occt_library
        import zencad.gui.util
        path = zencad.gui.util.pythonocc_core_directory()
        if path is None:
            print("PythonOCC is not installed")
            return -1
        install_precompiled_occt_library(tgtpath=path)
        return 0

    from zencad.showapi import widget_creator
    import zenframe.starter as frame

    frame.invoke(
        pargs,
        frame_creator=frame_creator,
        exec_top_half=top_half,
        exec_bottom_half=widget_creator)


if __name__ == "__main__":
    main()
