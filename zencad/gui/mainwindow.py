# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
from zencad.gui.inotifier import InotifyThread

import zencad.lazifier
import zencad.opengl

import zencad.unbound.communicator
import zencad.gui.actions

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

QMARKER_MESSAGE = "Press 'Q' to set marker"
WMARKER_MESSAGE = "Press 'W' to set marker"
DISTANCE_DEFAULT_MESSAGE = "Distance between markers"

__TRACE_COMMUNICATION__ = False

class InfoWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.infolay = QHBoxLayout()

		self.poslbl = QLabel("Tracking disabled")
		self.poslbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.poslbl.setAlignment(Qt.AlignCenter)

		self.marker1Label = QLabel(QMARKER_MESSAGE)
		self.marker1Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.marker1Label.setStyleSheet(
			"QLabel { background-color : rgb(100,0,0); color : white; }"
		)
		self.marker1Label.setAlignment(Qt.AlignCenter)

		self.marker2Label = QLabel(WMARKER_MESSAGE)
		self.marker2Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.marker2Label.setStyleSheet(
			"QLabel { background-color : rgb(0,100,0); color : white; }"
		)
		self.marker2Label.setAlignment(Qt.AlignCenter)

		self.markerDistLabel = QLabel(DISTANCE_DEFAULT_MESSAGE)
		self.markerDistLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.markerDistLabel.setAlignment(Qt.AlignCenter)

		self.infoLabel = QLabel("")
		self.infoLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.infoLabel.setAlignment(Qt.AlignCenter)
		#show_label(self.infoLabel, False)

		self.infolay.addWidget(self.poslbl)
		self.infolay.addWidget(self.marker1Label)
		self.infolay.addWidget(self.marker2Label)
		self.infolay.addWidget(self.markerDistLabel)
		self.infolay.addWidget(self.infoLabel)

		self.infolay.setContentsMargins(0,0,0,0)
		self.infolay.setSpacing(0)

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.setLayout(self.infolay)


class MainWindow(QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
	def __init__(self, client_communicator):
		super().__init__()
		self.openlock = threading.Lock()
		self.console = zencad.console.ConsoleWidget()
		self.texteditor = zencad.texteditor.TextEditor()
		self.current_opened = None

		self.client_communicator = client_communicator
		self.client_communicator.newdata.connect(self.new_worker_message)
		self.client_communicator.start_listen()

		self.cw = QWidget()
		self.cw_layout = QVBoxLayout()
		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)
		self.info_widget = InfoWidget()

		self.cw_layout.addWidget(self.hsplitter)
		self.cw_layout.addWidget(self.info_widget)
		self.cw.setLayout(self.cw_layout)
		
		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(QWidget())
		self.vsplitter.addWidget(self.console)

		self.resize(1000,800)

		self.cw_layout.setContentsMargins(0,0,0,0)
		self.cw_layout.setSpacing(0)
		self.setCentralWidget(self.cw)

		self.createActions()
		self.createMenus()
		self.createToolbars()

		self.set_start_file_as_current_opened()

		self.notifier = InotifyThread(self)
		self.notifier.changed.connect(self.reopen_current)
		self.notifier.retarget(self.current_opened)

	def new_worker_message(self, data):
		data = pickle.loads(data)
		cmd = data["cmd"]

		if __TRACE_COMMUNICATION__:
			print("MainWindow:communicator:", data)

		# TODO: Переделать в словарь
		if cmd == "hello": print("HelloWorld")
		elif cmd == 'bindwin': self.bind_window(winid=data['id'])
		elif cmd == 'setopened': self.set_current_opened(path=data['path'])
		elif cmd == 'clientpid': self.clientpid = data['pid']
		elif cmd == "qmarker": self.marker_handler("q", data)
		elif cmd == "wmarker": self.marker_handler("w", data)

	def marker_handler(self, qw, data):
		fmt='.5f'
		x = data["x"]; y = data["y"]; z = data["z"];
		idx = "Q" if qw else "W"
		print("{0}: x:{1}, y:{2}, z:{3}; point({1},{2},{3})".format(
			idx, format(x, fmt), format(y, fmt), format(z, fmt)))

	def bind_window(self, winid):
		container = QWindow.fromWinId(winid)
		cc = QWidget.createWindowContainer(container)
		self.vsplitter.replaceWidget(0, cc)
		self.client_communicator.send("unwait")

	def replace_widget(self, wdg):
		self.vsplitter.replaceWidget(0, wdg)

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)
	
	def set_start_file_as_current_opened(self):
		self.set_current_opened(sys.argv[0])

	def closeEvent(self, event):
		self.client_communicator.send({"cmd": "stopworld"})
		time.sleep(0.01)

	def reopen_current(self):
		self._open_routine(self.current_opened)

	def _open_routine(self, path):
		self.openlock.acquire()

		self.set_current_opened(path)

		self.client_communicator.send({"cmd": "stopworld"})
		self.client_communicator.stop_listen()

		lbl = QLabel("Loading... Maybe it crashed... Maybe not.")
		lbl.setAlignment(Qt.AlignCenter)
		lbl.setStyleSheet("QLabel { background-color : darkBlue; color : yellow; }");
		self.replace_widget(lbl)
    	
		self.client_communicator = zencad.unbound.application.start_unbounded_worker(path)
		self.client_communicator.start_listen()

		self.client_communicator.newdata.connect(self.new_worker_message)
		
		self.notifier.retarget(path)
		self.openlock.release()
