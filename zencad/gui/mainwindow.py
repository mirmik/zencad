# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
import zencad.gui.nqueue
from zencad.gui.inotifier import InotifyThread
from zencad.gui.infolabel import InfoWidget

import zencad.lazifier
import zencad.opengl

import zencad.gui.communicator
import zencad.gui.actions

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import signal
import multiprocessing
import time
import math
import threading
import os
import pickle
import sys
import signal
import random

MAIN_COMMUNICATOR = None
DISPLAY_WINID = None

__TRACE_COMMUNICATION__ = False

class ScreenWidget(QWidget):
	def __init__(self):
		super().__init__()

	def paintEvent(self, ev):
		pathes = ["techpriest.jpg"]

		painter = QPainter(self)
		painter.setPen(QColor(137,40,151))
		painter.setBrush(QColor(218,216,203))
		painter.drawRect(0,0,self.width(),self.height())
		bird = QImage(os.path.join(zencad.moduledir, random.choice(pathes)))
		
		bw = bird.width()
		bh = bird.height()
		w = self.width()
		h = self.height()
		kw = bw / w
		kh = bh / h

		if kh >= kw:
			bw = bw / kh
			cw = self.width() / 2
			painter.drawImage(QRect(cw-bw/2,0,bw,self.height()), bird)
		else:
			bh = bh / kw
			ch = self.height() / 2
			painter.drawImage(QRect(0,ch-bh/2,self.width(),bh), bird)


		font = QFont()
		font.setPointSize(12)
		painter.setFont(font)
		message = "Loading... please wait."
		painter.drawText(
			QPoint(
				self.width()/2 - QFontMetrics(font).width(message)/2,
				QFontMetrics(font).height()), 
			message)
		painter.end()

def info(*args):
	print("GUI:", *args)

class MainWindow(QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
	def __init__(self, 
			client_communicator=None, 
			openned_path=None, 
			presentation=False,
			fastopen=None,
			display_mode=False,
			title = "ZenCad"):
		super().__init__()
		self.setWindowTitle(title)
		self.openlock = threading.Lock()
		self.console = zencad.gui.console.ConsoleWidget()
		self.texteditor = zencad.gui.texteditor.TextEditor()
		self.current_opened = None
		self.last_reopen_time = time.time()
		self.need_prescale = True

		self.nqueue = zencad.gui.nqueue.nqueue()
		self.client_communicator = client_communicator
		
		if self.client_communicator:
			self.client_communicator.newdata.connect(self.new_worker_message)
			self.client_communicator.start_listen()
		self.sleeped_client = zencad.gui.application.spawn_sleeped_client(1)

		self.cw = QWidget()
		self.cw_layout = QVBoxLayout()
		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)
		self.info_widget = InfoWidget()

		self.cw_layout.addWidget(self.hsplitter)
		self.cw_layout.addWidget(self.info_widget)
		self.cw.setLayout(self.cw_layout)
		
		self.resize(1000,800)

		lbl = ScreenWidget()

		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(lbl)
		self.vsplitter.addWidget(self.console)

		self.vsplitter.setSizes([self.height()*5/8, self.height()*3/8])
		self.hsplitter.setSizes([self.width()*3/8, self.width()*5/8])

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
			self.presentation_mode = False
		#	self.set_presentation_label()

		self.fscreen_mode=False
		self.oldopenned = self.current_opened
		self.last_location = None
		self.session_id=0
		self.cc_window =None

		self.open_in_progress = False

		if fastopen:
			self._open_routine(fastopen)

		if display_mode:
			self.displayMode()

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
		try:
			cmd = data["cmd"]
		except:
			return

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
		elif cmd == "console": self.internal_console_request(data["data"])
		elif cmd == "trackinfo": self.info_widget.set_tracking_info(data["data"])
		#elif cmd == "screenshot_return": self.screen_return(data["data"])
		#elif cmd == "settitle": self.setWindowTitle(data["arg"])
		else:
			print("Warn: unrecognized command", data)

	def marker_handler(self, qw, data):
		fmt='.5f'
		x = data["x"]; y = data["y"]; z = data["z"];
		idx = qw.upper()
		print("{0}: x:{1}, y:{2}, z:{3}; point({1},{2},{3})".format(
			idx, format(x, fmt), format(y, fmt), format(z, fmt)))

		self.info_widget.set_marker_data(qw, x, y, z)

	def internal_console_request(self, data):
		self.console.write(data)

	def bind_window(self, winid, pid, session_id):
		with self.openlock:
			if session_id != self.session_id:
				return
	
			container = QWindow.fromWinId(winid)
			self.cc = QWidget.createWindowContainer(container)
			#self.cc.setAttribute( Qt.WA_TransparentForMouseEvents )
	
			self.cc_window = winid
			self.vsplitter.replaceWidget(0, self.cc)
			self.client_communicator.send("unwait")
			self.client_pid = pid
			self.setWindowTitle(self.current_opened)
	
			#info("window bind success: winid:{} file:{}".format(winid, self.current_opened))
			info("window bind success")
			if not self.need_prescale and self.last_location is not None:
				self.client_communicator.send({"cmd":"location", "dct": self.last_location})
				info("restore saved eye location")
	
			self.open_in_progress = False


	def replace_widget(self, wdg):
		self.vsplitter.replaceWidget(0, wdg)

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)

	def closeEvent(self, event):
		if self.client_communicator:
			self.client_communicator.send({"cmd": "stopworld"})
		if self.sleeped_client:
			self.sleeped_client.send({"cmd":"stopworld"})
		time.sleep(0.05)
		if self.client_communicator:
			self.client_communicator.kill()
		if self.sleeped_client:
			self.sleeped_client.kill()
		

	def reopen_current(self):
		if time.time() - self.last_reopen_time > 0.25:
			self._open_routine(self.current_opened)
			self.last_reopen_time = time.time()

	def _open_routine(self, path):
		print()
		info("open: file:{}".format(path))
		self.setWindowTitle(path)

		self.presentation_mode = False
		self.openlock.acquire()

		self.need_prescale = self.oldopenned != path
		self.oldopenned = path

		self.set_current_opened(path)

		if self.open_in_progress is True:
			self.client_communicator.stop_listen()
			time.sleep(0.05)
			self.client_communicator.kill()
			self.nqueue.add(self.client_communicator)
			self.client_communicator = None

		if self.cc_window and self.open_in_progress is False:
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
			time.sleep(0.05)
			self.client_communicator.kill()
	
		self.session_id += 1

		#self.sleeped_client = None
		if self.sleeped_client:
			self.client_communicator = self.sleeped_client
			self.client_communicator.send({"path":path, "need_prescale":self.need_prescale})
			self.sleeped_client = zencad.gui.application.spawn_sleeped_client(self.session_id + 1)

		else:
			self.client_communicator = zencad.gui.application.start_unbounded_worker(path, 
				need_prescale = self.need_prescale, session_id=self.session_id)

		self.client_communicator.start_listen()
		self.client_communicator.newdata.connect(self.new_worker_message)

		self.notifier.retarget(path)
		self.open_in_progress = True
		self.openlock.release()

	def screen(self):
		screen = QGuiApplication.primaryScreen()
		p = screen.grabWindow(self.cc_window)

		self.client_communicator.send({"cmd":"screenshot"})
		self.client_communicator.wait()

		btes, size = self.client_communicator.rpc_buffer()		
		return QPixmap.fromImage(QImage(btes, size[0], size[1], QImage.Format.Format_RGBA8888).mirrored(False,True))

	def location_update_handle(self, dct):
		scale = dct["scale"]
		eye = dct["eye"]
		center = dct["center"]

		self.last_location = dct

	def internal_key_pressed(self, s):
		if s == "F11": self.fullScreen()
		elif s == "F10": self.displayMode() 