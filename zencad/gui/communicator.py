#!/usr/bin/env python3

import os
import sys
import io
import base64
import json
import threading
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import PyQt5.QtCore as QtCore

import os
import signal
from zencad.util import print_to_stderr

import zencad.configuration


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
        self.subproc = None
        self.ifile = ifile
        self.ofile = ofile

        self.send({"cmd": "set_opposite_pid", "data": os.getpid()})

    def socket_notifier_handle(self, a):
        try:
            inputdata = self.ifile.readline()
            if len(inputdata) == 0:
                self.oposite_clossed.emit()
                return

            if zencad.configuration.COMMUNICATOR_TRACE:
                print_to_stderr("recv", inputdata)

            unwraped_data = json.loads(inputdata)

            if unwraped_data["cmd"] == "set_opposite_pid":
                self.declared_opposite_pid = unwraped_data["data"]
                return

            self.newdata.emit(unwraped_data, self.subproc_pid())

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
        self.sock_notifier = QtCore.QSocketNotifier(
            self.ifile.fileno(),
            QtCore.QSocketNotifier.Read,
            self
        )

        self.sock_notifier.activated.connect(self.socket_notifier_handle)

    def subproc_pid(self):
        """ PID процесса на той стороне можно узнать двумя путями.
        Либо это pid связанный с объектом subprocess, связанным с ним, 
        либо, если этот объект отсутствует, можно воспользоваться
        переданной кем-либо информацией о таком процессе. 
        Иногда процедура возвращает None. Это значит, что процесс на той стороне не был создан
        через subprocess и никто не успел уведомить коммуникатор о его pid."""
        return self.subproc.pid if self.subproc else self.declared_opposite_pid

    def send(self, obj):
        if zencad.configuration.COMMUNICATOR_TRACE:
            print_to_stderr("send", obj)

        sendstr = json.dumps(obj) + "\n"

        try:
            self.ofile.write(sendstr)
            self.ofile.flush()
            return True
        except Exception as ex:
            return False
