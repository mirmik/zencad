# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
import zencad.gui.startwdg
import zencad.gui.communicator
import zencad.gui.actions
import zencad.gui.retransler
import zencad.gui.signal_handling
from zencad.util import set_process_name

import zencad.lazifier
import zencad.opengl

from zencad.animate import AnimateThread

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from zencad.util import print_to_stderr

import psutil
import multiprocessing
import os
import sys
import threading
import time
import pickle
import runpy
import subprocess

STDIN_FILENO = 0
STDOUT_FILENO = 1

from zencad.gui.mainwindow import MainWindow

import zencad.configure
import zencad.settings

__DEBUG_MODE__ = False

INTERPRETER = sys.executable
RETRANSLATE_THREAD = None
MAIN_COMMUNICATOR = None
CONSOLE_RETRANS_THREAD = None

DISPLAY_WIDGET = None

def trace(*argv):
	if zencad.configure.CONFIGURE_APPLICATION_TRACE:
		print_to_stderr("APPTRACE: {}".format(str(argv)))

def traced(func):
	#def decor(*argv, **kwargs):
	#	trace(func.__name__, argv, kwargs)
	#	return func(*argv, **kwargs)
	return func

@traced
def start_main_application(tgtpath=None, presentation=False, display_mode=False, console_retrans=False):
	"""Запустить графический интерфейс в текущем потоке.

	Используются файловые дескрипторы по умолчанию, которые длжен открыть
	вызывающий поток."""

	set_process_name("zencad")
	trace("start_main_application", tgtpath, presentation, display_mode, console_retrans)	

	app = QApplication([])
	zencad.gui.signal_handling.setup_qt_interrupt_handling()

	zencad.opengl.init_opengl()
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + "/../industrial-robot.svg"))
	
	#TODO: Настройка цветов.
#	pal = app.palette()
#	pal.setColor(QPalette.Window, QColor(160, 161, 165))
#	app.setPalette(pal)

	#trace("START MAIN Communicator ????")
	#global MAIN_COMMUNICATOR
	#MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(ipipe=0, opipe=1)

	trace("START MAIN WIDGET")
	if presentation == False:	
		communicator_out = 1

		if console_retrans:
			trace("start_main_application::console_retrans")			
			zencad.gui.application.CONSOLE_RETRANS_THREAD = zencad.gui.retransler.console_retransler()
			zencad.gui.application.CONSOLE_RETRANS_THREAD.start()
			communicator_out = 3

		zencad.gui.application.MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(
			ipipe=zencad.gui.application.STDIN_FILENO, opipe=communicator_out)
		#zencad.gui.application.MAIN_COMMUNICATOR.start_listen()

		mw = MainWindow(
			client_communicator=
				MAIN_COMMUNICATOR,
			openned_path=tgtpath,
			display_mode=display_mode)

	else:
		if zencad.settings.list()["gui"]["start_widget"] == "true":
			strt_dialog = zencad.gui.startwdg.StartDialog()
			strt_dialog.exec()

			if strt_dialog.result() == 0:
				return

			openpath = strt_dialog.openpath

		else:
			openpath = zencad.gui.util.create_temporary_file(zencad_template=True)

		mw = MainWindow(
			presentation=False, 
			fastopen=openpath,
			display_mode=display_mode)

	mw.show()
	app.exec()
	trace("FINISH MAIN QTAPP")

	if zencad.gui.application.MAIN_COMMUNICATOR:
		zencad.gui.application.MAIN_COMMUNICATOR.stop_listen()

	time.sleep(0.05)

	procs = psutil.Process().children()	
	for p in procs:
		p.terminate()

	#psutil.wait_procs(procs, callback=on_terminate)

@traced
def start_application(tgtpath, debug):
	"""Запустить графическую оболочку в новом.

	Переданный пайп используется для коммуникации с процессом родителем
	3 и 4-ый файловые дескрипторы будут использоваться в новосозданной
	программе, поскольку она порождена отсюда.

	TODO: Следует убедиться, что файловые дескрипторы обрабатываются корректно
	TODO: Следует убедиться, что fd обрабатыаются корректно во всех ОС
	При необъодимости следует изменить алгоритм взаимодействия (Сокеты???)"""

	#i=os.dup(ipipe)
	#o=os.dup(opipe)
	#os.dup2(i, 3)
	#os.dup2(o, 4)

	debugstr = "--debug" if debug or __DEBUG_MODE__ else "" 
	interpreter = INTERPRETER
	cmd = '{} -m zencad --subproc {} --tgtpath "{}"'.format(interpreter, debugstr, tgtpath)

	subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	return subproc

@traced
def start_unbound_application(*args, tgtpath, debug = False, **kwargs):
	"""Основная процедура запуска.

	Создаёт в отдельном процессе графическую оболочку,
	После чего создаёт в своём процессе виджет, который встраивается в графическую оболочку.
	Для коммуникации между процессами создаётся pipe"""

	global MAIN_COMMUNICATOR

	subproc = start_application(tgtpath, debug)

	communicator = zencad.gui.communicator.Communicator(
		ipipe=subproc.stdout.fileno(), opipe=subproc.stdin.fileno())

	MAIN_COMMUNICATOR = communicator

	communicator.subproc = subproc

	common_unbouded_proc(pipes=True, need_prescale=True, *args, **kwargs)

@traced
def start_worker(path, sleeped=False, need_prescale=False, session_id=0):
	"""Создать новый поток и отправить запрос на добавление
	его вместо предыдущего ??? 

	TODO: Дополнить коментарий с подробным описанием механизма."""
	
	prescale = "--prescale" if need_prescale else ""
	sleeped = "--sleeped" if sleeped else ""
	debug_mode = "--debug" if __DEBUG_MODE__ else ""
	interpreter = INTERPRETER

	cmd = '{interpreter} -m zencad "{path}" --replace {prescale} {debug_mode} {sleeped} --session_id {session_id}'.format(
		interpreter=interpreter, 
		path=path, 
		prescale=prescale, 
		sleeped=sleeped,
		debug_mode=debug_mode,
		session_id=session_id)
	
	subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	return subproc

@traced
def spawn_sleeped_client(session_id):
	return start_unbounded_worker("", session_id, False, True)

@traced
def start_unbounded_worker(path, session_id, need_prescale=False, sleeped=False):
	"""Запустить процесс, обсчитывающий файл path и 
	вернуть его коммуникатор."""

	subproc = start_worker(path, sleeped, need_prescale, session_id)

	communicator = zencad.gui.communicator.Communicator(
		ipipe=subproc.stdout.fileno(), opipe=subproc.stdin.fileno())

	communicator.subproc = subproc

	return communicator

@traced
def update_unbound_application(*args, **kwargs):
	common_unbouded_proc(pipes=True, *args, **kwargs)

def on_terminate(proc):
	trace("process {} finished with exit code {}".format(proc, proc.returncode))

@traced
def common_unbouded_proc(scene, 
	view=None,
	animate=None, 
	preanimate=None,
	close_handle=None,
	pipes=False, 
	need_prescale=False, 
	session_id=0,
	sleeped = False):
	"""Создание приложения клиента, управляющее логикой сеанса"""

	trace("common_unbouded_proc")

	THREAD_FINALIZER = None
	ANIMATE_THREAD = None
	global MAIN_COMMUNICATOR
	global DISPLAY_WIDGET

	app = QApplication([])
	zencad.gui.signal_handling.setup_qt_interrupt_handling()
	zencad.opengl.init_opengl()

	widget = zencad.gui.viewadaptor.DisplayWidget(
		scene=scene, 
		view=scene.viewer.create_view() if view is None else view, 
		need_prescale=need_prescale)
	DISPLAY_WIDGET = widget

	if pipes:
		zencad.gui.viewadaptor.bind_widget_signal(
			widget, MAIN_COMMUNICATOR)


		def smooth_stop_world():
			trace("common_unbouded_proc::smooth_stop_world")
			
			if ANIMATE_THREAD:
				ANIMATE_THREAD.finish()

			if close_handle:
				close_handle()

			#time.sleep(0.1)

			#procs = psutil.Process().children()
			#trace(procs)
			#psutil.wait_procs(procs, callback=on_terminate)

			#MAIN_COMMUNICATOR.stop_listen()
			
			#if CONSOLE_RETRANS_THREAD:
			#	CONSOLE_RETRANS_THREAD.finish()			
			
			class final_waiter_thr(QThread):
				def run(self):
					procs = psutil.Process().children()
					trace(procs)
					psutil.wait_procs(procs, callback=on_terminate)
					app.quit()

			nonlocal THREAD_FINALIZER
			THREAD_FINALIZER = final_waiter_thr()
			THREAD_FINALIZER.start()

			#trace("FINISH UNBOUNDED QTAPP : app quit on receive")
			#app.quit()
			#trace("app quit on receive... after")

		def stop_world():
			trace("common_unbouded_proc::stop_world")
			MAIN_COMMUNICATOR.stop_listen()
			if ANIMATE_THREAD:
				ANIMATE_THREAD.finish()

			if CONSOLE_RETRANS_THREAD:
				CONSOLE_RETRANS_THREAD.finish()			

			if close_handle:
				close_handle()

			trace("FINISH UNBOUNDED QTAPP : app quit on receive")
			app.quit()
			trace("app quit on receive... after")


		def receiver(data):
			trace("common_unbouded_proc::receiver")
			try:
				data = pickle.loads(data)
				trace(data)
				if data["cmd"] == "stopworld": 
					stop_world()
				elif data["cmd"] == "console":
					sys.stdout.write(data["data"])
				else:
					widget.external_communication_command(data)
			except Exception as ex:
				print_to_stderr("common_unbouded_proc::receiver", ex)

		MAIN_COMMUNICATOR.newdata.connect(receiver)
		MAIN_COMMUNICATOR.oposite_clossed.connect(stop_world)
		MAIN_COMMUNICATOR.smooth_stop.connect(smooth_stop_world)
		#time.sleep(2)
		MAIN_COMMUNICATOR.send({"cmd":"bindwin", "id":int(widget.winId()), "pid":os.getpid(), "session_id":session_id})
		#MAIN_COMMUNICATOR.wait()

	if animate:
		ANIMATE_THREAD = AnimateThread(
			widget=widget, 
			updater_function=animate)

		if preanimate:
			preanimate(widget, ANIMATE_THREAD)

		ANIMATE_THREAD.start()
	
		def animate_stop():
			ANIMATE_THREAD.finish()
		
		widget.widget_closed.connect(animate_stop)
		
	if close_handle:
		widget.widget_closed.connect(close_handle)

	if MAIN_COMMUNICATOR is not None:
		MAIN_COMMUNICATOR.start_listen()

	def _clossed():
		pass

	widget.widget_closed.connect(_clossed)

	widget.show()
	#widget.hide()
	app.exec()
	trace("FINISH UNBOUNDED QTAPP")

	trace("Wait childs ...")

	trace("list of threads: ", threading.enumerate())

	procs = psutil.Process().children()
	trace(procs)
	psutil.wait_procs(procs, callback=on_terminate)
	#for p in procs:
	#    p.terminate()
	#gone, alive = psutil.wait_procs(procs, timeout=3, callback=on_terminate)
	#for p in alive:
	#    p.kill()


	trace("Wait childs ... OK")
