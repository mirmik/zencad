import os
import sys

DEBUG_PROCESS_NAME = os.getpid()


def set_debug_process_name(str):
    global DEBUG_PROCESS_NAME
    DEBUG_PROCESS_NAME = str


def print_to_stderr(*args):
    sys.stderr.write(f"DEBUG {DEBUG_PROCESS_NAME}: ")
    sys.stderr.write(str(args))
    sys.stderr.write("\r\n")
    sys.stderr.flush()


def create_temporary_file():
    path = tempfile.mktemp(".py")

    if zencad_template:
        f = open(path, "w")
        f.write(
            "#!/usr/bin/env python3\n#coding: utf-8\n\n"
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
