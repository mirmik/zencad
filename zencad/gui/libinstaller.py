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
        super().__init__()
        vlayout = QtWidgets.QVBoxLayout()

        msgLabel = QtWidgets.QLabel(
            "ZenCad did not find some libraries. You can use that instrument to install it.")
        vlayout.addWidget(msgLabel)

        separ = QtWidgets.QFrame()
        separ.setFrameShape(QtWidgets.QFrame.HLine)
        vlayout.addWidget(separ)

        msgLabel = QtWidgets.QLabel("Lookup.")
        vlayout.addWidget(msgLabel)

        self.button4 = QtWidgets.QPushButton(f"Try to import libraries")
        vlayout.addWidget(self.button4)
        self.button4.clicked.connect(self.try_to_import)

        separ = QtWidgets.QFrame()
        separ.setFrameShape(QtWidgets.QFrame.HLine)
        vlayout.addWidget(separ)

        msgLabel = QtWidgets.QLabel("Install pythonocc.")
        vlayout.addWidget(msgLabel)

        self.button1 = QtWidgets.QPushButton(
            f"Install pythonocc-{__pythonocc_version__}")
        vlayout.addWidget(self.button1)
        self.button1.clicked.connect(self.install_pythonocc_handler)

        separ = QtWidgets.QFrame()
        separ.setFrameShape(QtWidgets.QFrame.HLine)
        vlayout.addWidget(separ)

        msgLabel = QtWidgets.QLabel("Install OCCT for current user only.")
        vlayout.addWidget(msgLabel)

        self.button0 = QtWidgets.QPushButton(
            f"Install OCCT-{__occt_version__} for current user (~/.local/lib/occt-{__occt_version__})")
        vlayout.addWidget(self.button0)
        self.button0.clicked.connect(self.install_occt_handler)

        self.button2 = QtWidgets.QPushButton(
            f"Add ~/.local/lib/occt-{__occt_version__} to user LD_LIBRARY_PATH")
        vlayout.addWidget(self.button2)
        self.button2.clicked.connect(self.add_local_library_path_to_bashrc)

        separ = QtWidgets.QFrame()
        separ.setFrameShape(QtWidgets.QFrame.HLine)
        vlayout.addWidget(separ)

        msgLabel = QtWidgets.QLabel(
            "Install OCCT for all users (root permissions needed).")
        vlayout.addWidget(msgLabel)

        self.button3 = QtWidgets.QPushButton(
            f"Install OCCT-{__occt_version__} for all user (/usr/local/lib)")
        vlayout.addWidget(self.button3)
        self.button3.clicked.connect(self.install_occt_handler_global)

        self.console = ConsoleWidget()
        vlayout.addWidget(self.console)

        self.setLayout(vlayout)
        self.resize(800, 600)

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

    def install_occt_handler(self):

        class do_install_occt_handler(QtCore.QThread):
            def __init__(self, wdg):
                super().__init__()
                self.wdg = wdg

            def run(self):
                print(f"Install OCCT-{__occt_version__} started.")
                self.wdg.disable_buttons()

                sts = 0
                try:
                    sts = install_precompiled_occt_library(
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

        self.thr = do_install_occt_handler(self)
        self.thr.start()

    def install_occt_handler_global(self):

        class do_install_occt_handler(QtCore.QThread):
            def __init__(self, wdg):
                super().__init__()
                self.wdg = wdg

            def run(self):
                print(f"Install OCCT-{__occt_version__} started.")
                self.wdg.disable_buttons()

                sts = 0
                try:
                    sts = install_precompiled_occt_library(
                        "/usr/local/lib", occt_version=__occt_version__)
                except Exception as ex:
                    pass
                self.wdg.enable_buttons()

                if sts == 0:
                    print(
                        f"Install OCCT-{__occt_version__} finished succesful.")
                else:
                    print(f"Install OCCT-{__occt_version__} failed.")

        self.thr = do_install_occt_handler(self)
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

    def enable_buttons(self):
        self.button0.setEnabled(True)
        self.button1.setEnabled(True)
        self.button3.setEnabled(True)
        self.button4.setEnabled(True)
        self.button2.setEnabled(True)

    def disable_buttons(self):
        self.button0.setEnabled(False)
        self.button1.setEnabled(False)
        self.button2.setEnabled(False)
        self.button3.setEnabled(False)
        self.button4.setEnabled(False)


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
