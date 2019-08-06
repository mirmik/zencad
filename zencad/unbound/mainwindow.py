# coding: utf-8

import zencad
import zencad.console
import zencad.texteditor
import zencad.viewadaptor
import zencad.lazifier
import zencad.opengl
import zencad.texteditor

import zencad.unbound.communicator
import zencad.unbound.actions

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import multiprocessing
import time
import threading
import os
import pickle
import sys
import signal

MAIN_COMMUNICATOR = None
DISPLAY_WINID = None

class MainWindow(QMainWindow, zencad.unbound.actions.mixin):
	def __init__(self, client_communicator):
		super().__init__()
		self.openlock = threading.Lock()
		self.console = zencad.console.ConsoleWidget()
		self.texteditor = zencad.texteditor.TextEditor()
		self.current_opened = None

		self.client_communicator = client_communicator
		self.client_communicator.newdata.connect(self.new_worker_message)
		self.client_communicator.start_listen()

		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)

		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(QWidget())
		self.vsplitter.addWidget(self.console)

		self.resize(800,600)
		self.setCentralWidget(self.hsplitter)

		self.createActions()
		self.createMenus()
		self.createToolbars()

		self.set_start_file_as_current_opened()

	def new_worker_message(self, data):
		data = pickle.loads(data)
		cmd = data["cmd"]

		print("MainWindow:communicator:", data)

		if cmd == "hello": print("HelloWorld")
		elif cmd == 'bindwin': self.bind_window(winid=data['id'])
		elif cmd == 'setopened': self.set_current_opened(path=data['path'])
		elif cmd == 'clientpid': self.clientpid = data['pid']

	def bind_window(self, winid):
		container = QWindow.fromWinId(winid)
		cc = QWidget.createWindowContainer(container)
		self.vsplitter.replaceWidget(0, cc)
		self.client_communicator.send("unwait")

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)
	
	def set_start_file_as_current_opened(self):
		self.set_current_opened(sys.argv[0])

	def closeEvent(self, event):
		print("closeEvent")
		#os.kill(self.clientpid, signal.SIGKILL)
		print("send")
		self.client_communicator.send({"cmd": "stopworld"})
		print("send...ok")
		time.sleep(0.01)