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


def console_options_handle():

    parser = zenframe.argparse.ArgumentParser()

    # Смотри аргументы в zenframe.ArgumentParser
    parser.add_argument("--install-libs", action="store_true",
                        help="Console dialog for install third-libraries")
    parser.add_argument("--install-occt-force", nargs="*",
                        default=None, help="Download and install libocct")
    parser.add_argument("--install-pythonocc-force", action="store_true",
                        help="Download and install pythonocc package")
    parser.add_argument("--yes", action="store_true")

    pargs = parser.parse_args()
    return pargs


def top_half(communicator):
    from zencad.lazifier import install_evalcahe_notication
    install_evalcahe_notication(communicator)


def frame_creator(openpath, initial_communicator, norestore, unbound):
    from zencad.gui.mainwindow import MainWindow
    from zencad.gui.startwdg import StartDialog
    from zencad.settings import Settings
    from zencad.gui.util import create_temporary_file

    if openpath is None and not unbound:
        if Settings.get(["gui", "start_widget"]):
            strt_dialog = StartDialog()
            strt_dialog.exec()

            if strt_dialog.result() == 0:
                return

            openpath = strt_dialog.openpath

        else:
            openpath = create_temporary_file(zencad_template=True)

    mainwindow = MainWindow(
        initial_communicator=initial_communicator,
        restore_gui=not norestore)

    return mainwindow, openpath


def main():
    pargs = console_options_handle()

    if pargs.install_libs:
        from zencad.geometry_core_installer import console_third_libraries_installer_utility
        console_third_libraries_installer_utility(yes=pargs.yes)
        sys.exit()

    if pargs.install_pythonocc_force:
        from zencad.geometry_core_installer import install_precompiled_python_occ
        install_precompiled_python_occ()
        return

    if pargs.install_occt_force is not None:
        from zencad.geometry_core_installer import install_precompiled_occt_library
        path = pargs.install_occt_force[0] if len(
            pargs.install_occt_force) > 0 else None
        install_precompiled_occt_library(tgtpath=path)
        return

    from zencad.showapi import widget_creator
    import zenframe.starter as frame

    frame.invoke(
        pargs,
        frame_creator=frame_creator,
        exec_top_half=top_half,
        exec_bottom_half=widget_creator)


if __name__ == "__main__":
    main()
