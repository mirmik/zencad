#!/usr/bin/env python3

import os
import sys
import pickle
import threading
import random
import socket

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Transler(QObject):
    class Listener(QThread):
        newdata = pyqtSignal(bytes)

        def __init__(self, parent, lsock):
            QObject.__init__(self, parent)
            self.lsock = lsock

        def run(self):
            try:
                while 1:
                    data = self.lsock.recv(512)
                    self.newdata.emit(data)
            except Exception as e:
                print(e)

    def __init__(self, parent, oposite=None):
        QObject.__init__(self, parent)

        self.rsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.wsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.callbacks = {"setoposite": self.setoposite}

        self.raddress = "/tmp/zencad-socket-" + str(
            random.randint(0, 9223372036854775807)
        )
        self.rsock.bind(self.raddress)

        if oposite is None:
            pass
        else:
            self.waddress = oposite
            self.wsock.connect(oposite)
            self.send("setoposite", (self.raddress,))

        self.listener = self.Listener(self, self.rsock)
        self.listener.newdata.connect(self.parse)
        self.listener.start()

    def setoposite(self, oposite):
        self.waddress = oposite
        self.wsock.connect(oposite)

    def get_apino(self):
        return self.raddress

    def send(self, cmd, args):
        try:
            self.wsock.send(pickle.dumps({"cmd": cmd, "args": args}))
        except:
            pass

    def parse(self, data):
        dct = pickle.loads(data)
        cmd = dct["cmd"]
        if not cmd in self.callbacks:
            print("WARNING: unregistred command", cmd)
        else:
            self.callbacks[cmd](*dct["args"])

    def log(self, data):
        self.send("log", args=(data,))

    def stop(self):
        self.rsock.close()
        self.wsock.close()
        self.listener.quit()


class ClientTransler(Transler):
    sync_signal = pyqtSignal()
    screen_signal = pyqtSignal(str)
    stopworld_signal = pyqtSignal()
    centering_signal = pyqtSignal()
    autoscale_signal = pyqtSignal()
    reset_signal = pyqtSignal()

    def __init__(self, parent, oposite=None):
        Transler.__init__(self, parent, oposite)

        self.callbacks["stopworld"] = lambda: self.stopworld_signal.emit()
        self.callbacks["sync"] = lambda: self.sync_signal.emit()


class ServerTransler(Transler):
    readytoshow_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, parent, oposite=None):
        Transler.__init__(self, parent, oposite)
        self.callbacks["readytoshow"] = lambda winid: self.readytoshow_signal.emit(
            winid
        )
        self.callbacks["log"] = lambda data: self.log_signal.emit(data)
