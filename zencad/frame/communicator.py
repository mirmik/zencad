#!/usr/bin/env python3

import os
import sys
import io
import base64
import json
import fcntl
import threading
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import PyQt5.QtCore as QtCore

import os
import signal
from zencad.frame.util import print_to_stderr

from zencad.frame.listener import Listener
from zencad.configuration import Configuration


class Communicator(QObject):
    """Объект обеспечивает связь между процессами, позволяя 
    передавать комманды и отладочный вывод между оболочком и 
    инстансами рабочих процессов.
    Связь обеспечивается через входной файл @ifile и 
    выходной @ofile.

    TODO: вынести subproc из коммуникатора.
    """

    oposite_clossed = pyqtSignal()
    newdata = pyqtSignal(dict, int)

    def __init__(self, ifile, ofile):
        super().__init__()
        self.declared_opposite_pid = None
        self.ifile = ifile
        self.ofile = ofile

        self.send({"cmd": "set_opposite_pid", "data": os.getpid()})

    def newdata_handler(self, inputdata):  
        if Configuration.COMMUNICATOR_TRACE:
            print_to_stderr("recv", inputdata)

        try:   
            unwraped_data = json.loads(inputdata)
    
            if unwraped_data["cmd"] == "set_opposite_pid":
                self.declared_opposite_pid = unwraped_data["data"]
                return
    
            self.newdata.emit(unwraped_data, self.declared_opposite_pid)

        except Exception as ex:
            print_to_stderr(ex)
            sys.exit()

    def simple_read(self):
        """Чтение из входного файла. Не должно вызываться после
        вызова метода start_listen"""
        inputdata = self.ifile.readline()
        return inputdata

    def bind_handler(self, function):
        """Подписать внешний метод на событие прихода
        очередной команды. Если подписчиков много, событие получат все."""
        self.newdata.connect(function)

    def start_listen(self):
        self._listener = Listener(self.ifile, self)
        self._listener.newdata.connect(self.newdata_handler)
        self._listener.start()

    def stop_listen(self):
        if self._listener:
            self._listener.stop()
            self._listener.wait()

    #    flag = fcntl.fcntl(self.ifile.fileno(), fcntl.F_GETFL)
    #    fcntl.fcntl(self.ifile.fileno(), fcntl.F_SETFL, flag | os.O_NONBLOCK)
    #    
    #    self.sock_notifier = QtCore.QSocketNotifier(
    #        self.ifile.fileno(),
    #        QtCore.QSocketNotifier.Read,
    #        self
    #    )
#
    #    self.sock_notifier.activated.connect(self.socket_notifier_handle)

    def send(self, obj):
        if Configuration.COMMUNICATOR_TRACE:
            print_to_stderr("send", obj)

        sendstr = json.dumps(obj) + "\r\n"

        try:
            self.ofile.write(sendstr)
            self.ofile.flush()
            return True
        except Exception as ex:
            print_to_stderr(ex)
            return False
