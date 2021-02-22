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


def protect_path(s):
    if s[0] == s[-1] and (s[0] == "'" or s[0] == '"'):
        return s[1:-1]
    return s


def console_options_handle():
    parser = argparse.ArgumentParser()

    parser.add_argument("--none", action="store_true")
    parser.add_argument("--unbound", action="store_true")
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--mainunbound", action="store_true")
    parser.add_argument("--prescale", action="store_true")
    parser.add_argument("--comdebug", action="store_true")
    parser.add_argument("--zenframe", action="store_true")
    parser.add_argument("--sleeped", action="store_true",
                        help="Don't use manualy. Create sleeped thread.")
    parser.add_argument("--size")
    parser.add_argument("paths", type=str, nargs="*", help="runned file")

    parser.add_argument("--no-restore", action="store_true")
    parser.add_argument("--no-sleeped", action="store_true",
                        help="Disable sleeped optimization")

    pargs = parser.parse_args()

    if pargs.comdebug:
        import zencad.frame.communicator
        zencad.frame.communicator.COMMUNICATOR_TRACE = True

    return pargs


def exec_main_window_process(pargs):
    """	Запускает графическую оболочку, которая управляет.
            Потоками с виджетами отображения. """

    import zencad.frame.mainwindow
    import zencad.util

    openpath = pargs.paths[0] if len(pargs.paths) > 0 else None

    zencad.frame.util.set_debug_process_name("MAIN")
    zencad.frame.mainwindow.start_application(
        openpath=openpath,
        none=pargs.none,
        unbound=pargs.mainunbound,
        norestore=pargs.no_restore,
        sleeped_optimization=not pargs.no_sleeped)


def exec_display_only(pargs):
    """ Режим запускает один единственный виджет.
        Простой режим, никакой ретрансляции команд, никаких биндов. """
    print("exec_display_only")
    exit(0)

    # if len(pargs.paths) != 1:
    #     raise Exception("Display mode invoked without path")

    # runpy.run_path(pargs.paths[0], run_name="__main__")


def exec_display_unbound(pargs):
    """ Запускает виджет отображения, зависимый от графической
            оболочки."""
    print("exec_display_unbound")
    exit(0)

    # if len(pargs.paths) != 1:
    #     raise Exception("Display unbound mode invoked without path")

    # size = (float(a) for a in pargs.size.split(","))

    # from zencad.gui.display_unbounded import unbound_worker_exec
    # unbound_worker_exec(
    #     path=pargs.paths[0],
    #     prescale=pargs.prescale,
    #     size=size,
    #     sleeped=pargs.sleeped)


def finish_procedure():
    procs = psutil.Process().children()
    for p in procs:
        p.terminate()

    for p in procs:
        p.wait()


def main():
    pargs = console_options_handle()

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
