#!/usr/bin/env python3

from zencad.geometry_core_installer import test_third_libraries, install_precompiled_python_occ, install_precompiled_occt_library
from zencad.version import __occt_version__, __pythonocc_version__
from zenframe.util import print_to_stderr
from zenframe.retransler import ConsoleRetransler
from zenframe.console import ConsoleWidget
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
import os
import sys
print("LibraryInstaller")


class LibraryInstaller(QtWidgets.QWidget):
    def __init__(self):
        self.buttons = []

        super().__init__()
        vlayout = QtWidgets.QVBoxLayout()
        self.vlayout = vlayout

        self.add_label(
            "ZenCad did not find some libraries. You can use that instrument to install it.")

        self.add_separator()
        self.add_label("Lookup.")
        self.add_button("Try to import libraries", self.try_to_import)

        self.add_separator()
        self.add_label("Install pythonocc.")
        self.add_button(
            f"Install pythonocc-{__pythonocc_version__}", self.install_pythonocc_handler)

        if sys.platform in ("linux", "linux2"):
            self.add_separator()
            self.add_label("Install OCCT for current user only.")
            self.add_button(
                f"Install OCCT-{__occt_version__} for current user (~/.local/lib/occt-{__occt_version__})", self.install_occt_handler)
            self.add_button(
                f"Add ~/.local/lib/occt-{__occt_version__} to user LD_LIBRARY_PATH", self.add_local_library_path_to_bashrc)

            self.add_separator()
            self.add_label(
                "Install OCCT for all users (root permissions needed).")
            self.add_button(
                f"Install OCCT-{__occt_version__} for all user (/usr/local/lib)", self.install_occt_handler_global)

        if sys.platform in ("win32"):
            self.add_separator()
            self.add_label("Install OCCT in pythonocc directory.")
            self.add_button(
                f"Install OCCT-{__occt_version__} for in pythonocc directory", self.install_occt_to_pythonocc)

        self.console = ConsoleWidget()
        vlayout.addWidget(self.console)

        self.setLayout(vlayout)
        self.resize(800, 600)

    def add_label(self, msg):
        lbl = QtWidgets.QLabel(msg)
        self.vlayout.addWidget(lbl)

    def add_button(self, label, handler):
        button = QtWidgets.QPushButton(label)
        self.vlayout.addWidget(button)
        button.clicked.connect(handler)
        self.buttons.append(button)

    def add_separator(self):
        separ = QtWidgets.QFrame()
        separ.setFrameShape(QtWidgets.QFrame.HLine)
        self.vlayout.addWidget(separ)

    def enable_buttons(self):
        for b in self.buttons:
            b.setEnabled(True)

    def disable_buttons(self):
        for b in self.buttons:
            b.setEnabled(False)

    def try_to_import(self):
        dct = test_third_libraries()
        print()
        # print(dct)
        if dct["pythonocc"] is False:
            print("pythonocc import fault.")
        else:
            path = dct["pythonocc"]
            print(f"pythonocc founded: {path}.")

        if dct["occt"] is None:
            pass
        else:
            if dct["occt"] is False:
                print("OCCT loading fault.")
            else:
                print("OCCT succesfually loaded.")

    def add_local_library_path_to_bashrc(self):

        our_path = os.path.expanduser(f"~/.local/lib/occt-{__occt_version__}")
        our_string = f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{our_path}"

        with open(os.path.expanduser("~/.bashrc"), "r") as f:
            for s in f.readlines():
                if our_string in s:
                    print("Already added.")
                    print("Don't forget to restart the your terminal.")

                    return

        with open(os.path.expanduser("~/.bashrc"), "a") as f:
            f.write("\r\n" + "\r\n" +
                    f"# Add local occt-{__occt_version__} instance (from zencad)" + "\r\n" + our_string + "\r\n")
            print("Succesfually added.")
            print("Don't forget to restart the your terminal.")

    class do_install_occt_handler(QtCore.QThread):
        def __init__(self, wdg, path):
            super().__init__()
            self.wdg = wdg
            self.path = path

        def run(self):
            print(f"Install OCCT-{__occt_version__} started.")
            self.wdg.disable_buttons()
            sts = 0
            try:
                sts = install_precompiled_occt_library(
                    self.path,
                    occt_version=__occt_version__)
            except Exception as ex:
                sts = -1
                print(ex)
            self.wdg.enable_buttons()
            if sts == 0:
                print(
                    f"Install OCCT-{__occt_version__} finished succesful.")
            else:
                print(f"Install OCCT-{__occt_version__} failed.")

    def install_occt_handler(self):
        self.thr = self.do_install_occt_handler(self, None)
        self.thr.start()

    def install_occt_handler_global(self):
        self.thr = self.do_install_occt_handler(self, "/usr/local/lib")
        self.thr.start()

    def install_occt_to_pythonocc(self):
        import zencad.gui.util

        path = zencad.gui.util.pythonocc_core_directory()
        if path is None:
            print("PythonOCC is not installed")
            return -1

        self.thr = self.do_install_occt_handler(self, path)
        self.thr.start()

    def install_pythonocc_handler(self):
        class do_install_pythonocc_handler(QtCore.QThread):
            def __init__(self, wdg):
                super().__init__()
                self.wdg = wdg

            def run(self):
                print(f"Install pythonocc-{__pythonocc_version__} started.")
                self.wdg.disable_buttons()
                sts = 0
                try:
                    sts = install_precompiled_python_occ(
                        occversion=__pythonocc_version__)
                except Exception as ex:
                    pass
                self.wdg.enable_buttons()

                if sts == 0:
                    print(
                        f"Install pythonocc-{__pythonocc_version__} finished succesful.")
                else:
                    print(f"Install pythonocc-{__pythonocc_version__} failed.")

        self.thr = do_install_pythonocc_handler(self)
        self.thr.start()


def doit():
    QAPP = QtWidgets.QApplication(sys.argv[1:])

    wdg = LibraryInstaller()
    wdg.show()

    timer = QtCore.QTimer()
    timer.start(200)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    wdg.try_to_import()
    QAPP.exec()


if __name__ == "__main__":
    doit()
