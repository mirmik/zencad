#!/usr/bin/env python3

from zencad.gui.qt_backend import configure_qt_platform
configure_qt_platform()

import zencad.gui.display
import zencad.showapi
import signal
import sys
import threading

from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zencad.gui.defaults import EVENT_LOOP_PULSE_MS


QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')


QAPP = None


def init_display_only_mode() -> zencad.gui.display.DisplayWidget:
    global QAPP

    if QAPP is not None:
        raise Exception("QApplication is inited early")

    QAPP = QtWidgets.QApplication(sys.argv[1:])
    zencad.showapi.DISPLAY = zencad.gui.display.DisplayWidget()


def exec_display_only_mode():
    zencad.showapi.DISPLAY.show()

    interrupted = []
    previous_sigint = None
    sigint_replaced = False
    signal_pulse = None
    if threading.current_thread() is threading.main_thread():
        previous_sigint = signal.getsignal(signal.SIGINT)

        if previous_sigint in (signal.SIG_DFL, signal.default_int_handler):
            def handle_sigint(signum, _frame):
                interrupted.append(signum)
                QAPP.quit()

            signal.signal(signal.SIGINT, handle_sigint)
            sigint_replaced = True

        # Python signal handlers run only when the interpreter regains
        # control.  A small Python-backed Qt timer lets SIGINT escape the
        # native Qt event loop even while the viewer is otherwise idle.
        signal_pulse = QtCore.QTimer(QAPP)
        signal_pulse.setInterval(EVENT_LOOP_PULSE_MS)
        signal_pulse.timeout.connect(lambda: None)
        signal_pulse.start()

    try:
        exit_code = QAPP.exec()
    finally:
        if signal_pulse is not None:
            signal_pulse.stop()
        if sigint_replaced:
            signal.signal(signal.SIGINT, previous_sigint)

    if interrupted:
        raise SystemExit(128 + interrupted[-1])
    raise SystemExit(exit_code)


if __name__ == "__main__":
    init_display_only_mode()

    my_box = BRepPrimAPI_MakeBox(10., 20., 30.).Shape()
    zencad.showapi.DISPLAY._display.DisplayShape(my_box, update=True)

    exec_display_only_mode()
