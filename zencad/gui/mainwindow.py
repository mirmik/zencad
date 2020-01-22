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
import zencad.settings

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from zencad.util import print_to_stderr

import signal
import multiprocessing
import time
import math
import threading
import os
import pickle
import sys
import signal
import string
import random
import psutil

MAIN_COMMUNICATOR = None
MAINWINDOW_PROCESS = False

import zencad.configure

def trace(*args):
	if zencad.configure.CONFIGURE_MAINWINDOW_TRACE:
		print_to_stderr("MAINWINDOW:", *args)

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

		bind_widget_flag = zencad.settings.get(["gui", "bind_widget"])
		if not bind_widget_flag == "false":
			message = "Loading... please wait."
		
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(message)/2,
					QFontMetrics(font).height()), 
				message)
		painter.end()

def info(*args):
	if zencad.configure.CONFIGURE_GUI_INFO:
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

		global MAINWINDOW_PROCESS
		MAINWINDOW_PROCESS = True
		zencad.util.PROCNAME = "mainw"

		self.setWindowTitle(title)
		self.openlock = QMutex()#threading.Lock()
		self.console = zencad.gui.console.ConsoleWidget()
		self.texteditor = zencad.gui.texteditor.TextEditor()
		self.current_opened = None
		self.cc = None
		self.last_reopen_time = time.time()
		self.need_prescale = True

		self.nqueue = zencad.gui.nqueue.nqueue()
		self.client_communicator = client_communicator
		
		if self.client_communicator:
			self.client_communicator.newdata.connect(self.new_worker_message)
			#self.client_communicator.start_listen()

		if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION:
			trace("preconstruct slepped client")
			self.sleeped_client = zencad.gui.application.spawn_sleeped_client(session_id=1)

		self.cw = QWidget()
		self.cw_layout = QVBoxLayout()
		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)
		self.info_widget = InfoWidget()

		self.cw_layout.addWidget(self.hsplitter)
		self.cw_layout.addWidget(self.info_widget)
		self.cw.setLayout(self.cw_layout)
		#self.resize(1000,800)

		lbl = ScreenWidget()

		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(lbl)
		self.vsplitter.addWidget(self.console)

		self.resize(640,480)
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

		#self.notifier = InotifyThread(self)
		#self.notifier.changed.connect(self.reopen_current)
		#if openned_path:
		#	self.notifier.retarget(self.current_opened)
		self.make_notifier(openned_path)

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
			self.restore_gui_state()
			self.displayMode()
		else:
			self.restore_gui_state()
		self._display_mode = display_mode

	def make_notifier(self, path=None):
		self.notifier = InotifyThread(self)
		self.notifier.changed.connect(self.reopen_current)
		
		if path:
			self.notifier.retarget(path)


	def restore_gui_state(self):
		if zencad.configure.CONFIGURE_NO_RESTORE:
			return
		hsplitter_position = zencad.settings.hsplitter_position_get()
		vsplitter_position = zencad.settings.vsplitter_position_get()
		wsize = zencad.settings.get(["memory","wsize"])
		if hsplitter_position: self.hsplitter.setSizes([int(s) for s in hsplitter_position])
		if vsplitter_position: self.vsplitter.setSizes([int(s) for s in vsplitter_position])
		if wsize: self.setGeometry(wsize)

	def store_gui_state(self):
		hsplitter_position = self.hsplitter.sizes()
		vsplitter_position = self.vsplitter.sizes()
		wsize = self.geometry()
		zencad.settings.set(["memory","hsplitter_position"], hsplitter_position)
		zencad.settings.set(["memory","vsplitter_position"], vsplitter_position)
		zencad.settings.set(["memory","wsize"], wsize)
		zencad.settings.store()

	def remake_sleeped_thread(self):
		self.sleeped_client.send({"cmd":"stopworld"})
		self.sleeped_client = zencad.gui.application.spawn_sleeped_client(self.session_id + 1)

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
		#print_to_stderr("new_worker_message")
		data = pickle.loads(data)
		try:
			cmd = data["cmd"]
		except:
			return

		trace("MainWindow:communicator: input message")

		# TODO: Переделать в словарь
		if cmd == "hello": print("HelloWorld")
		elif cmd == 'bindwin': self.bind_window(winid=data['id'], pid=data["pid"], session_id=data["session_id"])
		elif cmd == 'setopened': self.set_current_opened(path=data['path'])
		elif cmd == 'clientpid': self.clientpid = data['pid']
		elif cmd == "qmarker": self.marker_handler("q", data)
		elif cmd == "wmarker": self.marker_handler("w", data)
		elif cmd == "location": self.location_update_handle(data["loc"])
		elif cmd == "keypressed": self.internal_key_pressed(data["key"])
		elif cmd == "keypressed_raw": self.internal_key_pressed_raw(data["key"], data["modifiers"])
		elif cmd == "keyreleased_raw": self.internal_key_released_raw(data["key"], data["modifiers"])
		elif cmd == "console": self.internal_console_request(data["data"])
		elif cmd == "trackinfo": self.info_widget.set_tracking_info(data["data"])
		elif cmd == "finish_screen": self.finish_screen(data["data"][0], data["data"][1])
		#elif cmd == "screenshot_return": self.screen_return(data["data"])
		#elif cmd == "settitle": self.setWindowTitle(data["arg"])
		else:
			print("Warn: unrecognized command", data)

	def marker_handler(self, qw, data):
		fmt='.5f'
		x = data["x"]; y = data["y"]; z = data["z"];
		idx = qw.upper()
		print("{0}: x:{1}, y:{2}, z:{3}; point3({1},{2},{3})".format(
			idx, format(x, fmt), format(y, fmt), format(z, fmt)))

		self.info_widget.set_marker_data(qw, x, y, z)

	def internal_console_request(self, data):
		self.console.write(data)

	def bind_window(self, winid, pid, session_id):
		trace("bind_window")
		bind_widget_flag = zencad.settings.get(["gui", "bind_widget"])
		
		if not self.openlock.tryLock():
			return
		
		#	self.openlock.unlock()
		#	return

		try:
			if session_id != self.session_id:
				self.openlock.unlock()
				return
		
			if not bind_widget_flag == "false":
				trace("bind window")
				container = QWindow.fromWinId(winid)
				self.cc = QWidget.createWindowContainer(container)
				
				self.cc_window = winid
				trace("replace widget")
				self.vsplitter.replaceWidget(0, self.cc)
				self.update()
			
			self.client_pid = pid
			self.setWindowTitle(self.current_opened)
		
			#info("window bind success: winid:{} file:{}".format(winid, self.current_opened))
			info("window bind success")
			if not self.need_prescale and self.last_location is not None:
				self.client_communicator.send({"cmd":"location", "dct": self.last_location})
				info("restore saved eye location")
		
			self.open_in_progress = False
			self.client_communicator.send({"cmd":"resize"})
			self.client_communicator.send({"cmd":"redraw"})
			time.sleep(0.05)
			self.update()
		except Exception as ex:
			self.openlock.unlock()
			print_to_stderr("exception on window bind", ex)
		self.openlock.unlock()


	def replace_widget(self, wdg):
		self.vsplitter.replaceWidget(0, wdg)

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)

	def closeEvent(self, event):
		#if not self._display_mode:
		self.store_gui_state()

		trace("closeEvent")
		if self.cc:
			self.cc.close()

		if self.client_communicator and self.client_communicator is not zencad.gui.application.MAIN_COMMUNICATOR:
			trace("send stopworld")
			self.client_communicator.send({"cmd": "stopworld"})
		else:
			trace("send smooth_stopworld")
			self.client_communicator.send({"cmd": "smooth_stopworld"})

		if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION and self.sleeped_client:
			trace("send sleeped optimization stopworld")
			self.sleeped_client.send({"cmd":"stopworld"})
		
		#print_to_stderr("pre sleep")
		
		time.sleep(0.05)
		trace("closeEvent...terminate")
	
		procs = psutil.Process().children()	
		for p in procs:
			p.terminate()

		trace("closeEvent...ok")

		#print_to_stderr("post sleep")
		#if self.client_communicator and self.client_communicator is not zencad.gui.application.MAIN_COMMUNICATOR:
		#	if __TRACE__:
		#		print_to_stderr("self.client_communicator.kill()")
		#	self.client_communicator.kill()
#
		#if SLEEPED_OPTIMIZATION and self.sleeped_client:
		#	if __TRACE__:
		#		print_to_stderr("self.sleeped_client.kill()")
		#	self.sleeped_client.kill()
#
#
		#if zencad.gui.application.RETRANSLATE_THREAD:
		#	if __TRACE__:
		#		print_to_stderr("zencad.gui.application.RETRANSLATE_THREAD.finish()")
		#	zencad.gui.application.RETRANSLATE_THREAD.finish()

		#if self.client_pid:
		#	os.kill(self.client_pid, signal.SIGKILL)
		
	def showEvent(self, ev):
		trace("showEvent")
		if self.client_communicator:
			self.client_communicator.start_listen()

	def reopen_current(self):
		if time.time() - self.last_reopen_time > 0.5:
			self._open_routine(self.current_opened)
			self.last_reopen_time = time.time()

	def _open_routine(self, path):
		if not self.openlock.tryLock():
			return
		trace("_open_routine")

		info("")
		info("open: file:{}".format(path))
		self.setWindowTitle(path)

		self.presentation_mode = False

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
			success = self.client_communicator.send({"cmd":"screenshot"})
			if success:
				self.openlock.unlock()
				return

		self.openlock.unlock()
		self.open_bottom_half()

	def open_bottom_half(self):
		trace("open_bottom_half")

		if not self.openlock.tryLock():
			return
		path = self.current_opened

		if self.client_communicator:
			if self.client_communicator is not zencad.gui.application.MAIN_COMMUNICATOR:
				self.client_communicator.send({"cmd": "stopworld"})
				self.client_communicator.stop_listen()
				time.sleep(0.05)
				self.client_communicator.kill()
				if sys.platform != "win32" and sys.platform != "win64":
					os.wait()

			else:
				self.client_communicator.send({"cmd": "smooth_stopworld"})
				time.sleep(0.05)
	
		self.session_id += 1

		if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION and self.sleeped_client:
			trace("unsleep procedure")
			self.client_communicator = self.sleeped_client
			success = self.client_communicator.send({"path":path, "need_prescale":self.need_prescale})
			if not success:
				self.client_communicator = zencad.gui.application.start_unbounded_worker(path, 
					need_prescale = self.need_prescale, session_id=self.session_id)
			self.sleeped_client = zencad.gui.application.spawn_sleeped_client(self.session_id + 1)
			time.sleep(0.05)

		else:
			self.client_communicator = zencad.gui.application.start_unbounded_worker(path, 
				need_prescale = self.need_prescale, session_id=self.session_id)

		self.client_communicator.newdata.connect(self.new_worker_message)
		self.client_communicator.start_listen()
		
		trace("client_communicator, fd:", self.client_communicator.ipipe, self.client_communicator.opipe)
		zencad.settings.Settings.add_recent(os.path.abspath(path))

		# Если уведомления включены, обновить цель
		if self.notifier:
			self.notifier.retarget(path)
		
		self.openlock.unlock()

	
	def finish_screen(self, data, size):
		btes, size = data, size#self.client_communicator.rpc_buffer()		
		screen = QPixmap.fromImage(QImage(btes, size[0], size[1], QImage.Format.Format_RGBA8888).mirrored(False,True))

		#if self.open_in_progress == False:
		#	return
		
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

		#if self.open_in_progress == False:
		#	return

		self.replace_widget(self.screen_label)
		self.open_bottom_half()

	def location_update_handle(self, dct):
		scale = dct["scale"]
		eye = dct["eye"]
		center = dct["center"]

		self.last_location = dct

	def internal_key_pressed(self, s):
		if s == "F11": self.fullScreen()
		elif s == "F10": self.displayMode() 

	def internal_key_pressed_raw(self, key, modifiers):
		#print("internal_key_pressed_raw")
		#if ((modifiers & (int(Qt.AltModifier | Qt.ControlModifier))) == 0) and (chr(key) in set(string.printable)):
		#	event = QInputMethodEvent()
		#	event.setCommitString(chr(key))
		#	QGuiApplication.sendEvent(self.texteditor, event);

		event = QKeyEvent(QEvent.KeyPress, key, Qt.KeyboardModifier(modifiers));
		QGuiApplication.postEvent(self.texteditor, event);

	def internal_key_released_raw(self, key, modifiers):
		event = QKeyEvent(QEvent.KeyRelease, key, Qt.KeyboardModifier(modifiers));
		QGuiApplication.postEvent(self.texteditor, event);
