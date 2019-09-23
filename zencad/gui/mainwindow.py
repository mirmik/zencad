# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
from zencad.gui.inotifier import InotifyThread
from zencad.gui.infolabel import InfoWidget

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

__TRACE_COMMUNICATION__ = False

class MainWindow(QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
	def __init__(self, client_communicator=None, openned_path=None, presentation=False):
		super().__init__()
		self.openlock = threading.Lock()
		self.console = zencad.gui.console.ConsoleWidget()
		self.texteditor = zencad.gui.texteditor.TextEditor()
		self.current_opened = None


		self.client_communicator = client_communicator
		
		if self.client_communicator:
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
		
		if presentation:
			lbl = self.presentation_label() 
		else:
			lbl = QLabel()
			lbl.setFixedSize(700,500)
		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(lbl)
		self.vsplitter.addWidget(self.console)

		self.resize(1000,800)

		self.cw_layout.setContentsMargins(0,0,0,0)
		self.cw_layout.setSpacing(0)
		self.setCentralWidget(self.cw)

		self.createActions()
		self.createMenus()
		self.createToolbars()

		if openned_path:
			self.set_current_opened(openned_path)

		self.notifier = InotifyThread(self)
		self.notifier.changed.connect(self.reopen_current)
		
		if openned_path:
			self.notifier.retarget(self.current_opened)

		if presentation:
			self.presentation_mode = True
			self.texteditor.hide()
			self.console.hide()
		else:
			presentation_mode = False
		#	self.set_presentation_label()

		self.fscreen_mode=False
		self.oldopenned = self.current_opened
		self.last_location = None
		self.session_id=0
		self.cc_window =None

	def presentation_label(self):
		url = os.path.join(zencad.moduledir, "zencad_logo.png")
		img = QPixmap(url);

		painter = QPainter(img)
		painter.setPen(Qt.green)
		font = QFont()
		font.setPointSize(18)
		painter.setFont(font)
		message2 = """From the fact that you will create 3d models with scripts,\nnothing will change in your life, created with scripts but 3d models will be."""
		message = "Cad system for righteous Zen programmers. "
		painter.drawText(
			QPoint(
				20 ,
				img.height() - 20), 
			message)
		
		font = QFont()
		font.setPointSize(12)
		painter.setFont(font)
		painter.setPen(Qt.yellow)
		for i, s in enumerate(message2.splitlines()):
			painter.drawText(
			QPoint(
				20 ,
				img.height() - 25 - QFontMetrics(font).height()*(2-i)), 
			s)

		painter.end()

		label = QLabel();
		label.setPixmap(img);
		self.preslabel = label
		return label

	def new_worker_message(self, data):
		data = pickle.loads(data)
		cmd = data["cmd"]

		if __TRACE_COMMUNICATION__:
			print("MainWindow:communicator:", data)

		# TODO: Переделать в словарь
		if cmd == "hello": print("HelloWorld")
		elif cmd == 'bindwin': self.bind_window(winid=data['id'], pid=data["pid"], session_id=data["session_id"])
		elif cmd == 'setopened': self.set_current_opened(path=data['path'])
		elif cmd == 'clientpid': self.clientpid = data['pid']
		elif cmd == "qmarker": self.marker_handler("q", data)
		elif cmd == "wmarker": self.marker_handler("w", data)
		elif cmd == "location": self.location_update_handle(data["loc"])
		elif cmd == "keypressed": self.internal_key_pressed(data["key"])

	def marker_handler(self, qw, data):
		fmt='.5f'
		x = data["x"]; y = data["y"]; z = data["z"];
		idx = "Q" if qw else "W"
		print("{0}: x:{1}, y:{2}, z:{3}; point({1},{2},{3})".format(
			idx, format(x, fmt), format(y, fmt), format(z, fmt)))

		self.info_widget.set_marker_data(qw, x, y, z)

	def bind_window(self, winid, pid, session_id):
		if session_id != self.session_id:
			return

		container = QWindow.fromWinId(winid)
		self.cc = QWidget.createWindowContainer(container)
		#self.cc.setAttribute( Qt.WA_TransparentForMouseEvents )

		self.cc_window = winid
		self.vsplitter.replaceWidget(0, self.cc)
		self.client_communicator.send("unwait")
		self.client_pid = pid

		if self.oldopenned == self.current_opened and self.last_location is not None:
			self.client_communicator.send({"cmd":"location", "dct": self.last_location})

	def replace_widget(self, wdg):
		self.vsplitter.replaceWidget(0, wdg)

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)

	def closeEvent(self, event):
		if self.client_communicator:
			self.client_communicator.send({"cmd": "stopworld"})
		time.sleep(0.01)

	def reopen_current(self):
		self._open_routine(self.current_opened)

	def _open_routine(self, path):
		self.presentation_mode = False
		self.openlock.acquire()

		need_prescale = self.oldopenned != path
		self.oldopenned = path

		self.set_current_opened(path)

		if self.cc_window:
			screen = self.screen()
			painter = QPainter(screen)
			painter.setPen(Qt.green)
			font = QFont()
			font.setPointSize(12)
			painter.setFont(font)
			message = "Loading... please wait."
			painter.drawText(
				QPoint(
					screen.width()/2 - QFontMetrics(font).width(message)/2,
					QFontMetrics(font).height()), 
				message)
			painter.end()
	
			self.screen_label = QLabel()
			self.screen_label.setPixmap(screen)

			self.replace_widget(self.screen_label)

		if self.client_communicator:
			self.client_communicator.send({"cmd": "stopworld"})
			self.client_communicator.stop_listen()
	
		self.session_id += 1
		self.client_communicator = zencad.unbound.application.start_unbounded_worker(path, 
			need_prescale = need_prescale, session_id=self.session_id)

		self.client_communicator.start_listen()

		self.client_communicator.newdata.connect(self.new_worker_message)

		self.notifier.retarget(path)
		self.openlock.release()

	def screen(self):
		screen = QGuiApplication.primaryScreen()
		p = screen.grabWindow(self.cc_window)
		return p

	def location_update_handle(self, dct):
		scale = dct["scale"]
		eye = dct["eye"]
		center = dct["center"]

		self.last_location = dct
		#print("locinfo:", self.last_location)

	def internal_key_pressed(self, s):
		#print(s)

		if s == "F11": self.fullScreen()
		elif s == "F10": self.displayMode() 