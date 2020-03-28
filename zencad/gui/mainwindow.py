# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
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
from PyQt5.QtTest import *

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

class ScreenSaverWidget(QWidget):
	def __init__(self, text=None, color=QColor(137,40,151)):
		if text is None:
			text = "Loading... please wait."

		self.text = text
		self.subtext = ["", "", ""]
		self.color = color
		self.last_install_time = time.time()
		self.mode="techpriest"
		super().__init__()

	def set_background(self, bg):
		self.background_pixmap = bg
		#self.background_pixmap_dark = bg.copy(0,0,bg.width(),bg.height())


	def set_error_state(self):
		self.mode = "error"
		self.set_text("Error in loaded script")
		self.subtext=["","",""]

	def drop_background(self):
		self.background_pixmap = None

	def set_loading_state(self):
		self.mode = "load"
		if sys.platform == "darwin":
			self.set_text("Loading ... (embeding not supported for osx)")
		else:
			self.set_text("Loading ...")
		self.last_install_time = time.time()

	def set_text(self, text):
		self.text = text
		self.update()

	def set_subtext(self, lvl, text):
		self.subtext[lvl] = text
		self.update()

	def black_box_paint(self, ev):
		painter = QPainter(self)
		painter.setPen(Qt.white)
		
		if self.background_pixmap == None:
			painter.setBrush(Qt.black)
			painter.drawRect(0,0,self.width(),self.height())
		else:
			if time.time() - self.last_install_time < 0.7 and self.mode!="error":
				painter.drawPixmap(0,0,self.width(),self.height(), self.background_pixmap)
			else:
				painter.drawPixmap(0,0,self.width(),self.height(), self.background_pixmap)
				painter.fillRect(QRect(0, 0, self.width(), self.height()), QBrush(QColor(0, 0, 0, 200)))

		font = QFont()
		font.setPointSize(16)
		painter.setFont(font)
	
		message = self.text

		if time.time() - self.last_install_time > 0.7 or self.mode=="error":
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(message)/2,
					self.height()/2 - 1 * QFontMetrics(font).height()), 
					message)
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[0])/2,
					self.height()/2 + 0 *QFontMetrics(font).height()), 
					self.subtext[0])
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[1])/2,
					self.height()/2 + 1*QFontMetrics(font).height()), 
					self.subtext[1])
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[2])/2,
					self.height()/2 + 2*QFontMetrics(font).height()), 
					self.subtext[2])

		QTimer.singleShot(750, self.repaint)
		
	def basePaintEvent(self, ev):
		pathes = ["techpriest.jpg"]

		painter = QPainter(self)
		painter.setPen(self.color)
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
			message = self.text
		
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(message)/2,
					QFontMetrics(font).height()), 
				message)
		painter.end()

	def paintEvent(self, ev):
		if self.mode == "error":
			self.black_box_paint(ev)
		elif self.mode == "load":
			self.black_box_paint(ev)
		else: 
			self.basePaintEvent(ev)

def info(*args):
	if zencad.configure.CONFIGURE_GUI_INFO:
		print("GUI:", *args)

class KeyPressEater(QObject):
	def __init__(self):
		super().__init__()

	def eventFilter(self, obj, event):
		return False

class MainWindow(QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
	def __init__(self, 
			client_communicator=None, 
			openned_path=None, 
			fastopen=None,
			display_mode=False,
			title = "ZenCad"):
		super().__init__()

		trace("MAINWINDOW: constructor")

		global MAINWINDOW_PROCESS
		MAINWINDOW_PROCESS = True
		zencad.util.PROCNAME = f"mw({os.getpid()})"

		self.setWindowTitle(title)
		self.openlock = QMutex()
		self.opened_subproc = None
		#self.window = None
		self.winid = None
		self.console = zencad.gui.console.ConsoleWidget()
		self.texteditor = zencad.gui.texteditor.TextEditor()
		self.current_opened = None
		self.embeded_window =None
		self.embeded_window_container = None
		self.last_reopen_time = time.time()
		self.need_prescale = True

		self.client_finalization_list = []
		self.communicator_dictionary = {}

		self.client_communicator = client_communicator
		
		if self.client_communicator:
			self.client_communicator.newdata.connect(self.new_worker_message)

		if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION:
			trace("preconstruct slepped client")
			self.sleeped_client = zencad.gui.application.spawn_sleeped_client(session_id=1)

		trace("MAINWINDOW: create widgets")

		trace("MAINWINDOW: create central widget")
		self.cw = QWidget()
		self.cw_layout = QVBoxLayout()
		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)

		trace("MAINWINDOW: create InfoWidget")
		self.info_widget = InfoWidget()

		self.cw_layout.addWidget(self.hsplitter)
		self.cw_layout.addWidget(self.info_widget)
		self.cw.setLayout(self.cw_layout)

		trace("MAINWINDOW: create ScreenSaverWidget")
		self.screen_saver = ScreenSaverWidget()

		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(self.screen_saver)
		self.vsplitter.addWidget(self.console)

		self.resize(640,480)
		self.vsplitter.setSizes([self.height()*5/8, self.height()*3/8])
		self.hsplitter.setSizes([self.width()*3/8, self.width()*5/8])

		self.cw_layout.setContentsMargins(0,0,0,0)
		self.cw_layout.setSpacing(0)
		trace("MAINWINDOW: set central widget")
		self.setCentralWidget(self.cw)

		trace("MAINWINDOW: create menus")
		self.createActions()
		self.createMenus()
		self.createToolbars()

		if openned_path:
			trace(f"MAINWINDOW: set_current_opened {openned_path}")
			self.set_current_opened(openned_path)

		trace(f"MAINWINDOW: Make Notifier")
		self.make_notifier(openned_path)

		trace(f"MAINWINDOW: Is presentation mode?")

		self.fscreen_mode=False
		self.oldopenned = self.current_opened
		self.last_location = None
		self.session_id=0

		self.open_in_progress = False

		trace(f"MAINWINDOW: Is fastopen?")
		if fastopen:
			trace("FASTOPEN {}".format(fastopen))
			self._open_routine(fastopen, update_texteditor=True)

		self.restore_gui_state()
		
		trace(f"MAINWINDOW: Is display mode?")
		if display_mode:
			self.display_mode_enable(True)

		#self._display_mode = display_mode

		#self.evfilter = KeyPressEater()
		#self.installEventFilter(self.evfilter)

		trace("MAINWINDOW: finish constructor")

		#self.vsplitter.splitterMoved.connect(self.embeded_window_resized)
		#self.hsplitter.splitterMoved.connect(self.embeded_window_resized)

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
		texteditor_hidden = zencad.settings.get(["memory", "texteditor_hidden"]) == 'true'
		console_hidden = zencad.settings.get(["memory", "console_hidden"]) == 'true'
		wsize = zencad.settings.get(["memory","wsize"])
		if hsplitter_position: self.hsplitter.setSizes([int(s) for s in hsplitter_position])
		if vsplitter_position: self.vsplitter.setSizes([int(s) for s in vsplitter_position])
		if texteditor_hidden: self.hideEditor(True)
		if console_hidden: self.hideConsole(True)
		if wsize: self.setGeometry(wsize)

		w = self.hsplitter.width()
		h = self.vsplitter.height()
		if hsplitter_position[0]=="0" or hsplitter_position[0]=="1": self.hsplitter.setSizes([0.382*w, 0.618*w])
		if vsplitter_position[0]=="0" or vsplitter_position[1]=="0": self.vsplitter.setSizes([0.618*h, 0.382*h])


	def store_gui_state(self):
		hsplitter_position = self.hsplitter.sizes()
		vsplitter_position = self.vsplitter.sizes()
		wsize = self.geometry()
		zencad.settings.set(["memory","texteditor_hidden"], self.texteditor.isHidden())
		zencad.settings.set(["memory","console_hidden"], self.console.isHidden())
		zencad.settings.set(["memory","hsplitter_position"], hsplitter_position)
		zencad.settings.set(["memory","vsplitter_position"], vsplitter_position)
		zencad.settings.set(["memory","wsize"], wsize)
		zencad.settings.store()

	def remake_sleeped_thread(self):
		self.sleeped_client.send({"cmd":"stopworld"})
		self.sleeped_client = zencad.gui.application.spawn_sleeped_client(self.session_id + 1)

	#def presentation_label(self):
	#	url = os.path.join(zencad.moduledir, "zencad_logo.png")
	#	img = QPixmap(url);
#
	#	painter = QPainter(img)
	#	painter.setPen(Qt.green)
	#	font = QFont()
	#	font.setPointSize(18)
	#	painter.setFont(font)
	#	message2 = """From the fact that you will create 3d models with scripts,\nnothing will change in your life, created with scripts but 3d models will be."""
	#	message = "Cad system for righteous Zen programmers. "
	#	painter.drawText(
	#		QPoint(
	#			20 ,
	#			img.height() - 20), 
	#		message)
	#	
	#	font = QFont()
	#	font.setPointSize(12)
	#	painter.setFont(font)
	#	painter.setPen(Qt.yellow)
	#	for i, s in enumerate(message2.splitlines()):
	#		painter.drawText(
	#		QPoint(
	#			20 ,
	#			img.height() - 25 - QFontMetrics(font).height()*(2-i)), 
	#		s)
#
	#	painter.end()
#
	#	label = QLabel();
	#	label.setPixmap(img);
	#	self.preslabel = label
	#	return label

	def new_worker_message(self, data, procpid):
		data = pickle.loads(data)
		try:
			cmd = data["cmd"]
		except:
			print("Warn: new_worker_message: message without 'cmd' field")
			return

		if procpid != self.client_communicator.subproc_pid() and data["cmd"] != "finish_screen":
			trace("MAINWINDOW: message: procpid != self.client_communicator.subproc_pid", procpid, self.client_communicator.subproc_pid())
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
		elif cmd == "keypressed_raw": self.internal_key_pressed_raw(data["key"], data["modifiers"], data["text"])
		elif cmd == "keyreleased_raw": self.internal_key_released_raw(data["key"], data["modifiers"])
		elif cmd == "console": self.internal_console_request(data["data"])
		elif cmd == "trackinfo": self.info_widget.set_tracking_info(data["data"])
		elif cmd == "finish_screen": self.finish_screen(data["data"][0], data["data"][1], procpid)
		elif cmd == "fault": self.open_fault()
		elif cmd == "evalcache": self.evalcache_notification(data)
		else:
			print("Warn: unrecognized command", data)

	def evalcache_notification(self, data):
		if data["subcmd"] == "newtree":
			self.screen_saver.set_subtext(0, "Eval tree: objs:{objs} root:{root}".format(root=data["root"][:8], objs=data["len"]))
		if data["subcmd"] == "progress":
			self.screen_saver.set_subtext(1, "to load: {}".format(data["toload"]))
			self.screen_saver.set_subtext(2, "to eval: {}".format(data["toeval"]))

	def marker_handler(self, qw, data):
		fmt='.5f'
		x = data["x"]; y = data["y"]; z = data["z"];
		idx = qw.upper()
		print("{0}: x:{1}, y:{2}, z:{3}; point3({1},{2},{3})".format(
			idx, format(x, fmt), format(y, fmt), format(z, fmt)))

		self.info_widget.set_marker_data(qw, x, y, z)

	def internal_console_request(self, data):
		self.console.write(data)

	def subprocess_finalization_do(self):
		trace("subprocess_finalization_do")
		for comm in self.client_finalization_list:
			comm.send({"cmd":"stopworld"})

	#def embeded_window_resized(self, *args, **kwargs):
	#	print("embeded_window_resized")
	#	if self.embeded_window_container:
	#		self.blacklifier.setGeometry(self.embeded_window_container.geometry())
	#		#self.blacklifier.setParent(self.embeded_window_container)
	#		self.blacklifier.raise_()
			
	def is_window_binded(self):
		bind_widget_flag = zencad.settings.get(["gui", "bind_widget"])
		return not bind_widget_flag == "false" and not zencad.configure.CONFIGURE_NO_EMBEDING_WINDOWS


	def synchronize_subprocess_state(self):
		"""
			Пересылаем на ту сторону информацию об опциях интерфейса.
		"""
		size = self.vsplitter.widget(0).size()

		if not self.need_prescale and self.last_location is not None:
			self.client_communicator.send({"cmd":"location", "dct": self.last_location})
			info("restore saved eye location")
	
		if self.is_window_binded():
			self.client_communicator.send({"cmd":"resize", "size":(size.width(), size.height())})
		self.client_communicator.send({"cmd":"set_perspective", "en": self.perspective_checkbox_state})
		self.client_communicator.send({"cmd":"keyboard_retranslate", "en": not self.texteditor.isHidden()})
		self.client_communicator.send({"cmd":"redraw"})



	def bind_window(self, winid, pid, session_id):
		trace("bind_window: winid:{}, pid:{}".format(winid,pid))

		if self.client_communicator.subproc_pid() != pid:
			"""Если заявленный pid отправителя не совпадает с pid текущего коммуникатора,
			то бинд уже неактуален."""
			print("Nonactual bind")
			return
		
		if not self.openlock.tryLock():
			return

		try:
			if session_id != self.session_id:
				self.openlock.unlock()
				return
		
			if self.is_window_binded():
				#oldwindow = self.cc_window
				self.embeded_window = QWindow.fromWinId(winid)

				#oldcc = self.embeded_window_container
				self.embeded_window_container = QWidget.createWindowContainer(
					self.embeded_window)

				#self.embeded_window_container.installEventFilter(self.evfilter)
				
				#self.cc_window = winid
				trace("replace widget")
				self.vsplitter.replaceWidget(0, self.embeded_window_container)

				#if oldwindow is not None:
				#	wind = QWindow.fromWinId(oldwindow)
				#	if wind is not None:
				#		wind.close()					

				self.update()
			
			self.client_pid = pid
			self.setWindowTitle(self.current_opened)
		
			info("window bind success")
			self.open_in_progress = False

			self.synchronize_subprocess_state()

			time.sleep(0.1)
			self.update()
		except Exception as ex:
			self.openlock.unlock()
			print_to_stderr("exception on window bind", ex)
			raise ex

		self.subprocess_finalization_do()
		self.openlock.unlock()

	def replace_widget(self, wdg):
		if wdg is not self.vsplitter.widget(0):
			wdg.resize(self.vsplitter.widget(0).size())
			self.vsplitter.replaceWidget(0, wdg)

	def set_current_opened(self, path):
		self.current_opened = path
		self.texteditor.open(path)

	def closeEvent(self, event):
		self.store_gui_state()

		trace("closeEvent")
		if self.embeded_window_container:
			self.embeded_window_container.close()

		if self.client_communicator and self.client_communicator is not zencad.gui.application.MAIN_COMMUNICATOR:
			trace("send stopworld")
			self.client_communicator.send({"cmd": "stopworld"})
		else:
			trace("send smooth_stopworld")
			self.client_communicator.send({"cmd": "smooth_stopworld"})

		if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION and self.sleeped_client:
			trace("send sleeped optimization stopworld")
			self.sleeped_client.send({"cmd":"stopworld"})
		
		time.sleep(0.05)
		trace("closeEvent...terminate")
	
		procs = psutil.Process().children()	
		for p in procs:
			try:
				p.terminate()
			except psutil.NoSuchProcess as ex:
				pass

		trace("closeEvent...ok")
		
	def showEvent(self, ev):
		trace("showEvent")
		if self.client_communicator:
			self.client_communicator.start_listen()

	def reopen_current(self):
		#if time.time() - self.last_reopen_time > 0.7:
		self._open_routine(self.current_opened, False)
		self.texteditor.reopen()
		self.last_reopen_time = time.time()

	def delete_communicator(self):
		"""Вызывается по сигналу об окончании сеанса"""

		trace("delete_communicator")

		self.openlock.lock()
		
		comm = self.sender()
		comm.stop_listen()
		
		if comm in self.client_finalization_list:
			self.client_finalization_list.remove(comm)
		
		del self.communicator_dictionary[comm.subproc.pid]
		
		# clean client_finalization_list from uncostistent nodes
		for comm in self.client_finalization_list:
			if comm not in self.communicator_dictionary.values():
				self.client_finalization_list.remove(comm)

		trace("del from self.communicator_dictionary {}".format([ c.subproc.pid for c 
			in self.communicator_dictionary.values()]))

		comm.kill()
		#comm.subproc.wait()

		self.openlock.unlock()

	def _open_routine(self, path, update_texteditor=True):
		if not self.openlock.tryLock():
			return
		trace("_open_routine")

		info("")
		info("open: file:{}".format(path))
		self.setWindowTitle(path)

		self.presentation_mode = False

		self.need_prescale = self.oldopenned != path

		another_file = path != self.current_opened

		self.oldopenned = path
		self.current_opened = path

		if update_texteditor:
			self.texteditor.open(path)

		if self.open_in_progress is True:
			"""Процедура открытия была инициирована раньше,
			чем прошлый открываемый скрипт отчитался об успешном завершении"""
			self.client_communicator.kill()
			self.client_finalization_list.append(self.client_communicator)

		if another_file:
			self.screen_saver.drop_background()

		if self.embeded_window and self.open_in_progress is False:
			if not another_file and zencad.configure.CONFIGURE_SCREEN_SAVER_TRANSLATE:
				self.client_communicator.send({"cmd":"screenshot"})
			self.client_communicator.send({"cmd":"stop_activity"})
			self.client_finalization_list.append(self.client_communicator)

		trace("planned to finalize:", len(self.client_finalization_list))

		self.console.clear()
		path = self.current_opened
		
		try:
			self.session_id += 1
			if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION and self.sleeped_client:
				""" Будим спящую заготовку """
				trace("unsleep procedure")
				self.client_communicator = self.sleeped_client
				size = self.vsplitter.widget(0).size()
				size = "{},{}".format(size.width(), size.height())
				success = self.client_communicator.send({"path":path, "need_prescale":self.need_prescale, "size":size})
				if not success:
					"""Если разбудить заготовку не удалось, просто создать новый процесс"""
					trace("NOT SUCCESS UNSLEEP ROUTINE")
					self.client_communicator = zencad.gui.application.start_unbounded_worker(path, 
						need_prescale = self.need_prescale, session_id=self.session_id, size=self.vsplitter.widget(0).size())
				# Инициируем создание новой заготовки.
				self.sleeped_client = zencad.gui.application.spawn_sleeped_client(self.session_id + 1)
				time.sleep(0.05)
	
			else:
				""" Если оптимизация не включена, то просто создать новый процесс. """
				self.client_communicator = zencad.gui.application.start_unbounded_worker(path, 
					need_prescale = self.need_prescale, session_id=self.session_id, size=self.vsplitter.widget(0).size())

		except OSError as ex:
			print("Err: open error")
			return

		# Теперь новый клиент готов к работе.
		self.open_in_progress = True
		self.communicator_dictionary[self.client_communicator.subproc.pid] = self.client_communicator
		trace("add to self.communicator_dictionary", [c for c in self.communicator_dictionary])
		self.client_communicator.oposite_clossed.connect(self.delete_communicator)
		self.client_communicator.newdata.connect(self.new_worker_message)
		self.client_communicator.start_listen()
		
		# Добавляем путь в список последних вызовов.
		zencad.settings.Settings.add_recent(os.path.abspath(path))

		self.screen_saver.set_loading_state()
		# Сплиттер некоректно отработает, до первого showEvent
		if hasattr(self, "MARKER"):
			timeout = 100 if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION else 500
			old_window_container = self.embeded_window_container
			def foo():
				self.openlock.lock()
				if self.open_in_progress:
					self.replace_widget(self.screen_saver)
				if old_window_container is not None:
					old_window_container.close()
				self.openlock.unlock()

			if self.is_window_binded():
				QTimer.singleShot(timeout, foo)
		self.MARKER=None

		# Если уведомления включены, обновить цель.
		if self.notifier:
			self.notifier.retarget(path)
		
		self.update_recent_menu()

		self.openlock.unlock()

	#def resizeEvent(self, ev):
	#	super().resizeEvent(ev)
		#self.embeded_window_resized()

	def open_fault(self):
		self.screen_saver.set_error_state()

	def finish_screen(self, data, size, procpid):
		self.openlock.lock()
		btes, size = data, size		
		self.last_screen = QPixmap.fromImage(QImage(btes, size[0], size[1], QImage.Format_RGBA8888).mirrored(False,True))
		self.screen_saver.set_background(self.last_screen)
		self.openlock.unlock()

	def location_update_handle(self, dct):
		scale = dct["scale"]
		eye = dct["eye"]
		center = dct["center"]

		self.last_location = dct


	def internal_key_pressed_raw(self, key, modifiers, text):
		self.texteditor.setFocus();
		event = QKeyEvent(QEvent.KeyPress, key, Qt.KeyboardModifier(modifiers), text);
		QGuiApplication.postEvent(self.texteditor, event);
		
	def internal_key_released_raw(self, key, modifiers):
		event = QKeyEvent(QEvent.KeyRelease, key, Qt.KeyboardModifier(modifiers));
		QGuiApplication.postEvent(self.texteditor, event);
