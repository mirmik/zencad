#!/usr/bin/env python3

import zencad.gui.display
import zencad.showapi
import sys

from OCC.Display.backend import load_pyqt5, load_backend
from OCC.Display.backend import get_qt_modules
import OCC.Core.BRepPrimAPI

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zenframe.configuration import Configuration
if Configuration.FILTER_QT_WARNINGS:
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
    QAPP.exec()
    sys.exit()


if __name__ == "__main__":
    init_display_only_mode()

    my_box = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(10., 20., 30.).Shape()
    zencad.showapi.DISPLAY._display.DisplayShape(my_box, update=True)

    exec_display_only_mode()
