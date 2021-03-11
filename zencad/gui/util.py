from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import tempfile


def create_temporary_file(zencad_template=False):
    path = tempfile.mktemp(".py")

    if zencad_template:
        f = open(path, "w")
        f.write(
            "#!/usr/bin/env python3\n#coding: utf-8\n\nfrom zencad import *\n\nm=box(10)\ndisp(m)\n\nshow()\n"
        )
        f.close()

    return path


def open_file_dialog(parent, directory=""):
    filters = "*.py;;*.*"
    defaultFilter = "*.py"

    if directory == tempfile.gettempdir():
        directory = "."

    path = QFileDialog.getOpenFileName(
        parent, "Open File", directory, filters, defaultFilter
    )

    return path


def save_file_dialog(parent):
    filters = "*.py;;*.*"
    defaultFilter = "*.py"

    path = QFileDialog.getSaveFileName(
        parent, "Save File", "", filters, defaultFilter
    )

    return path


def open_online_manual():
    QDesktopServices.openUrl(
        QUrl("https://mirmik.github.io/zencad", QUrl.TolerantMode)
    )


def pythonocc_directory():
    try:
        import OCC
    except:
        return None

    return os.path.dirname(OCC.__file__)


def pythonocc_core_directory():
    try:
        import OCC.Core
    except:
        return None

    return os.path.dirname(OCC.Core.__file__)