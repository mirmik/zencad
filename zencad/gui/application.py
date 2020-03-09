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
import io
import sys
import threading
import time
import signal
import pickle
import runpy
import subprocess

STDIN_FILENO = 0
STDOUT_FILENO = 1

from zencad.gui.mainwindow import MainWindow

import zencad.configure
import zencad.settings

INTERPRETER = sys.executable
RETRANSLATE_THREAD = None
MAIN_COMMUNICATOR = None
CONSOLE_RETRANS_THREAD = None
APPLICATION = None
IS_STARTER = False

DISPLAY_WIDGET = None

def trace(*argv):
	if zencad.configure.CONFIGURE_APPLICATION_TRACE:
		print_to_stderr("APPTRACE: {}".format(str(argv)))



def start_main_application(tgtpath=None, presentation=False, display_mode=False, console_retrans=False):
	"""Запустить графический интерфейс в текущем потоке.

	Используются файловые дескрипторы по умолчанию, которые длжен открыть
	вызывающий поток."""

	set_process_name("zencad")
	trace("start_main_application", tgtpath, presentation, display_mode, console_retrans)	

	def signal_sigchild(a,b):
		os.wait()

	if sys.platform == "linux":
		signal.signal(signal.SIGCHLD, signal_sigchild) 

	app = QApplication([])
	zencad.gui.signal_handling.setup_qt_interrupt_handling()
	zencad.opengl.init_opengl()
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + "/../industrial-robot.svg"))

	trace("START MAIN WIDGET")
	if presentation == False:	
		# Если режим презентации отключен, это значит, что уже существует окно,
		# которое мы сразу можем биндить.

		communicator_out_file = sys.stdout

		if console_retrans:
			trace("start_main_application::console_retrans")			
			zencad.gui.application.CONSOLE_RETRANS_THREAD = zencad.gui.retransler.console_retransler(sys.stdout)
			zencad.gui.application.CONSOLE_RETRANS_THREAD.start()
			communicator_out_file = zencad.gui.application.CONSOLE_RETRANS_THREAD.new_file

		trace(f"Create MAIN_COMMUNICATOR: ipipe:{zencad.gui.application.STDIN_FILENO} opipe:{communicator_out_file.fileno()}")
		zencad.gui.application.MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(
			ifile=sys.stdin, ofile=communicator_out_file)

		trace("Create MainWindow")
		mw = MainWindow(
			client_communicator=
				MAIN_COMMUNICATOR,
			openned_path=tgtpath,
			display_mode=display_mode)

	else:
		# Приложение запускается в одиночестве. Без подпроцесса.
		# Если разрешено, создаём стартовый диалог. 
		# Если нет, создаём временный файл.

		trace("EXEC (StartDialog)")

		if zencad.settings.list()["gui"]["start_widget"] == "true":
			strt_dialog = zencad.gui.startwdg.StartDialog()
			strt_dialog.exec()

			if strt_dialog.result() == 0:
				return

			openpath = strt_dialog.openpath

		else:
			openpath = zencad.gui.util.create_temporary_file(zencad_template=True)

		mw = MainWindow(
			fastopen=openpath,
			display_mode=display_mode)

	trace("Show MainWindow")
	mw.show()
	
	trace("APP EXEC (MainWindow)")
	app.exec()
	trace("FINISH MAIN QTAPP")

	trace("MAIN_COMMUNICATOR stop listen")
	if zencad.gui.application.MAIN_COMMUNICATOR:
		zencad.gui.application.MAIN_COMMUNICATOR.stop_listen()

	time.sleep(0.05)

	trace("terminate process")
	procs = psutil.Process().children()	
	for p in procs:
		try:
			p.terminate()
		except psutil.NoSuchProcess:
			pass


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

	no_cache = "--no-cache" if zencad.configure.CONFIGURE_DISABLE_LAZY else "" 
	debugstr = "--debug" if debug or zencad.configure.DEBUG_MODE else "" 
	debugcomm = "--debugcomm" if zencad.configure.CONFIGURE_PRINT_COMMUNICATION_DUMP else ""
	no_sleeped = "" if zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION else "--disable-sleeped"
	no_evalcache_notify = "--no-evalcache-notify" if zencad.configure.CONFIGURE_WITHOUT_EVALCACHE_NOTIFIES else ""
	interpreter = INTERPRETER
	cmd = f'{interpreter} -m zencad {no_sleeped} {no_cache} --subproc {debugstr} --tgtpath {tgtpath} {no_evalcache_notify} {debugcomm}"'

	subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, 
		close_fds=True)
	return subproc


def start_unbound_application(*args, tgtpath, debug = False, **kwargs):
	"""Основная процедура запуска.

	Создаёт в отдельном процессе графическую оболочку,
	После чего создаёт в своём процессе виджет, который встраивается в графическую оболочку.
	Для коммуникации между процессами создаётся pipe"""

	global MAIN_COMMUNICATOR
	global IS_STARTER

	IS_STARTER = True
	zencad.util.PROCNAME = f"st({os.getpid()})"

	subproc = start_application(tgtpath, debug)

	stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
	stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

	communicator = zencad.gui.communicator.Communicator(
		ifile=stdout, ofile=stdin)

	MAIN_COMMUNICATOR = communicator
	communicator.subproc = subproc

	common_unbouded_proc(pipes=True, need_prescale=True, *args, **kwargs)


def start_worker(path, sleeped=False, need_prescale=False, session_id=0, size=None):
	"""Создать новый поток и отправить запрос на добавление
	его вместо предыдущего ??? 

	TODO: Дополнить коментарий с подробным описанием механизма."""
	
	no_cache = "--no-cache" if zencad.configure.CONFIGURE_DISABLE_LAZY else "" 
	prescale = "--prescale" if need_prescale else ""
	sleeped = "--sleeped" if sleeped else ""
	debug_mode = "--debug" if zencad.configure.DEBUG_MODE else ""
	debugcomm_mode = "--debugcomm" if zencad.configure.CONFIGURE_PRINT_COMMUNICATION_DUMP else ""
	no_evalcache_notify = "--no-evalcache-notify" if zencad.configure.CONFIGURE_WITHOUT_EVALCACHE_NOTIFIES else ""
	sizestr = "--size {},{}".format(size.width(), size.height()) if size is not None else ""
	interpreter = INTERPRETER

	cmd = f'{interpreter} -m zencad "{path}" --replace {prescale} {no_cache} {no_evalcache_notify} {debug_mode} {debugcomm_mode} {sleeped} {sizestr} --session_id {session_id}'
	
	try:
		subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, 
			close_fds=True)
		return subproc
	except OSError as ex:
		print("Warn: subprocess.Popen finished with exception", ex)
		raise ex


def spawn_sleeped_client(session_id):
	return start_unbounded_worker("", session_id, False, True)


def start_unbounded_worker(path, session_id, need_prescale=False, sleeped=False, size=None):
	"""Запустить процесс, обсчитывающий файл path и 
	вернуть его коммуникатор."""

	trace("start_unbounded_worker")
	subproc = start_worker(path, sleeped, need_prescale, session_id, size=size)

	stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
	stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

	communicator = zencad.gui.communicator.Communicator(
		ifile=stdout, ofile=stdin)
	communicator.subproc = subproc

	return communicator


def update_unbound_application(*args, **kwargs):
	zencad.util.PROCNAME = f"un({os.getpid()})"
	common_unbouded_proc(pipes=True, *args, **kwargs)

def on_terminate(proc):
	trace("process {} finished with exit code {}".format(proc, proc.returncode))


def common_unbouded_proc(scene, 
	view=None,
	animate=None, 
	preanimate=None,
	close_handle=None,
	pipes=False, 
	need_prescale=False, 
	session_id=0,
	sleeped = False,
	size=None):
	"""Создание приложения клиента, управляющее логикой сеанса"""

	trace("common_unbouded_proc")

	THREAD_FINALIZER = None
	ANIMATE_THREAD = None
	global MAIN_COMMUNICATOR
	global DISPLAY_WIDGET
	global APPLICATION

	app = QApplication([])
	APPLICATION = app
	zencad.gui.signal_handling.setup_qt_interrupt_handling()
	zencad.opengl.init_opengl()

	widget = zencad.gui.viewadaptor.DisplayWidget(
		scene=scene, 
		view=scene.viewer.create_view() if view is None else view, 
		need_prescale=need_prescale,
		bind_mode = pipes,
		session_id = session_id,
		communicator = MAIN_COMMUNICATOR)
	DISPLAY_WIDGET = widget

	if size:
		widget.resize(QSize(size[0], size[1]))

	if pipes:
		zencad.gui.viewadaptor.bind_widget_signal(
			widget, MAIN_COMMUNICATOR)

		def smooth_stop_world():
			trace("common_unbouded_proc::smooth_stop_world")
			
			if ANIMATE_THREAD:
				ANIMATE_THREAD.finish()

			if close_handle:
				close_handle()
			
			class final_waiter_thr(QThread):
				def run(self):
					procs = psutil.Process().children()
					trace(procs)
					psutil.wait_procs(procs, callback=on_terminate)
					app.quit()

			nonlocal THREAD_FINALIZER
			THREAD_FINALIZER = final_waiter_thr()
			THREAD_FINALIZER.start()

		def stop_world():
			trace("common_unbouded_proc::stop_world")
			if IS_STARTER:
				return smooth_stop_world()

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

		def stop_activity():
			"""
			Prepare to finalization.
			Stop animation.
			Invoke finalization handle."""
			trace("common_unbouded_proc::stop_activity")

			if ANIMATE_THREAD:
				ANIMATE_THREAD.finish()

			if close_handle:
				close_handle()


		def receiver(data):
			trace("common_unbouded_proc::receiver")
			try:
				data = pickle.loads(data)
				trace(data)
				if data["cmd"] == "stopworld": 
					stop_world()
				elif data["cmd"] == "smooth_stopworld": 
					smooth_stop_world()
				elif data["cmd"] == "stop_activity":
					stop_activity()
				elif data["cmd"] == "console":
					sys.stdout.write(data["data"])
				else:
					widget.external_communication_command(data)
			except Exception as ex:
				print_to_stderr("common_unbouded_proc::receiver", ex)

		MAIN_COMMUNICATOR.newdata.connect(receiver)
		MAIN_COMMUNICATOR.oposite_clossed.connect(stop_world)
		MAIN_COMMUNICATOR.smooth_stop.connect(smooth_stop_world)
	
		
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

	trace("APP EXEC (DisplayWidget)")
	app.exec()

	trace("FINISH UNBOUNDED QTAPP")
	trace("Wait childs ...")
	trace("list of threads: ", threading.enumerate())

	procs = psutil.Process().children()
	trace(procs)
	psutil.wait_procs(procs, callback=on_terminate)

	trace("Wait childs ... OK")

def quit():
	if APPLICATION:
		APPLICATION.quit()