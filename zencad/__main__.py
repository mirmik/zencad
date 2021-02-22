#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import time
import argparse
import psutil
import traceback
import runpy
import signal

from zencad.configuration import Configuration
from zencad.frame.finisher import setup_interrupt_handlers, finish_procedure

def protect_path(s):
    if s[0] == s[-1] and (s[0] == "'" or s[0] == '"'):
        return s[1:-1]
    return s


def console_options_handle():
    parser = argparse.ArgumentParser()

    parser.add_argument("--install-libs", action="store_true",
                        help="Console dialog for install third-libraries")
    parser.add_argument("--install-occt-force", nargs="*",
                        default=None, help="Download and install libocct")
    parser.add_argument("--install-pythonocc-force", action="store_true",
                        help="Download and install pythonocc package")
    parser.add_argument("--yes", action="store_true")

    parser.add_argument("--none", action="store_true")
    parser.add_argument("--zenframe", action="store_true", help="Test frame sublibrary")
    parser.add_argument("--unbound", action="store_true")
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--mainunbound", action="store_true")
    parser.add_argument("--prescale", action="store_true")
    parser.add_argument("--sleeped", action="store_true",
                        help="Don't use manualy. Create sleeped thread.")
    parser.add_argument("--size")
    parser.add_argument("paths", type=str, nargs="*", help="runned file")

    parser.add_argument("--no-restore", action="store_true")
    parser.add_argument("--no-sleeped", action="store_true",
                        help="Disable sleeped optimization")

    pargs = parser.parse_args()
    return pargs


def exec_main_window_process(pargs):
    """	Запускает графическую оболочку, которая управляет.
            Потоками с виджетами отображения. """

    import zencad.gui.mainwindow
    import zencad.frame.util

    openpath = pargs.paths[0] if len(pargs.paths) > 0 else None

    zencad.frame.util.set_debug_process_name("MAIN")
    zencad.gui.mainwindow.start_application(
        openpath=openpath,
        none=pargs.none,
        unbound=pargs.mainunbound,
        norestore=pargs.no_restore,
        sleeped_optimization=not pargs.no_sleeped)


def exec_display_only(pargs):
    """ Режим запускает один единственный виджет.
        Простой режим, никакой ретрансляции команд, никаких биндов. """

    if len(pargs.paths) != 1:
        raise Exception("Display mode invoked without path")

    runpy.run_path(pargs.paths[0], run_name="__main__")


def exec_display_unbound(pargs):
    """ Запускает виджет отображения, зависимый от графической
            оболочки."""

    if len(pargs.paths) != 1:
        raise Exception("Display unbound mode invoked without path")

    size = (float(a) for a in pargs.size.split(","))

    from zencad.gui.display_unbounded import unbound_worker_exec
    unbound_worker_exec(
        path=pargs.paths[0],
        prescale=pargs.prescale,
        size=size,
        sleeped=pargs.sleeped)

def main():
    setup_interrupt_handlers()
    pargs = console_options_handle()

    if Configuration.TRACE_EXEC_OPTION:
        from zencad.frame.util import print_to_stderr
        print_to_stderr(pargs)

    # TEST ZENFRAME
    if (pargs.zenframe): 
        import zencad.frame.main
        zencad.frame.main.main()

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

    try:
        # Удаляем кавычки из пути, если он есть
        if len(pargs.paths) > 0:
            pargs.paths[0] = protect_path(pargs.paths[0])

        if pargs.display:
            exec_display_only(pargs)

        elif pargs.unbound:
            exec_display_unbound(pargs)

        else:
            exec_main_window_process(pargs)

    except Exception as ex:
        from zencad.frame.util import print_to_stderr
        print_to_stderr(f"Finished with exception", ex)
        print_to_stderr(f"Exception class: {ex.__class__}")
        traceback.print_exc()

    finish_procedure()


if __name__ == "__main__":
    main()
