import io
import os
import time
import subprocess
import sys
from zencad import print_to_stderr

#from zencad.gui.retransler import ConsoleRetransler
from zencad.gui.communicator import Communicator
from zencad.gui.retransler import ConsoleRetransler
from zencad.gui.display import DisplayWidget

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

import zencad.configuration
if zencad.configuration.FILTER_QT_WARNINGS:
    QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')

def spawn_main_process(path):
    interpreter = sys.executable

    cmd = f'{interpreter} -m zencad "{path}" --mainunbound'

    try:
        subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                   close_fds=True)
        return subproc
    except OSError as ex:
        print("Warn: subprocess.Popen finished with exception", ex)
        raise ex

def start_unbounded_main(path):
    subproc = spawn_main_process(path)

    stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
    stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

    communicator = Communicator(ifile=stdout, ofile=stdin)
    communicator.subproc = subproc

    return communicator


BIND_MODE = True

def _show(scene):    
    QAPP = QtWidgets.QApplication([])
    CONSOLE_FILTER = ConsoleRetransler(sys.stdout)
    CONSOLE_FILTER.start2()
    
    maincomm = start_unbounded_main(sys.argv[0])
    
    time.sleep(2)

    display = DisplayWidget(
        bind_mode=True,
        communicator=maincomm,
        init_size=(640,480))
    display.attach_scene(scene)
    
    # todo: почему не внутри?
    maincomm.bind_handler(display.external_communication_command)
    maincomm.oposite_clossed.connect(QtWidgets.QApplication.instance().quit)
    maincomm.start_listen()
    
    if BIND_MODE:
        maincomm.send({
            "cmd": "bindwin",
            "id": int(display.winId()),
            "pid": os.getpid(),
        })
    display.show()
    
    time.sleep(0.05)
    timer = QtCore.QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.
    
    QtWidgets.QApplication.instance().exec()
