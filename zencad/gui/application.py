# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor
import zencad.gui.startwdg
import zencad.gui.communicator
import zencad.gui.actions

import zencad.lazifier
import zencad.opengl

from zencad.animate import AnimateThread

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import setproctitle
import multiprocessing
import os
import sys
import time
import pickle
import runpy

from zencad.gui.mainwindow import MainWindow

__TRACED__= False

INTERPRETER = sys.executable
RETRANSLATE_THREAD = None
MAIN_COMMUNICATOR = None

def trace(*argv):
	if __TRACED__:
		print("APPTRACE: {}".format(str(argv)))

def traced(func):
	def decor(*argv, **kwargs):
		trace(func.__name__, argv, kwargs)
		return func(*argv, **kwargs)
	return decor

@traced
def start_main_application(tgtpath=None, presentation=False, display_mode=False):
	"""Запустить графический интерфейс в текущем потоке.

	Используются файловые дескрипторы по умолчанию, которые длжен открыть
	вызывающий поток."""

	setproctitle.setproctitle("zencad")

	app = QApplication([])
	
	zencad.opengl.init_opengl()
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + "/../industrial-robot.svg"))
	
	#TODO: Настройка цветов.
#	pal = app.palette()
#	pal.setColor(QPalette.Window, QColor(160, 161, 165))
#	app.setPalette(pal)

	if presentation == False:	
		mw = MainWindow(
			client_communicator=
				zencad.gui.communicator.Communicator(ipipe=3, opipe=4),
			openned_path=tgtpath,
			display_mode=display_mode)
		mw.show()

	else:
		strt_dialog = zencad.gui.startwdg.StartDialog()
		strt_dialog.exec()

		if strt_dialog.result() == 0:
			return

		mw = MainWindow(
			presentation=False, 
			fastopen=strt_dialog.openpath,
			display_mode=display_mode)

	mw.show()
	app.exec()
	trace("FINISH MAIN QTAPP")

@traced
def start_application(ipipe, opipe, tgtpath):
	"""Запустить графическую оболочку в новом.

	Переданный пайп используется для коммуникации с процессом родителем
	3 и 4-ый файловые дескрипторы будут использоваться в новосозданной
	программе, поскольку она порождена отсюда.

	TODO: Следует убедиться, что файловые дескрипторы обрабатываются корректно
	TODO: Следует убедиться, что fd обрабатыаются корректно во всех ОС
	При необъодимости следует изменить алгоритм взаимодействия (Сокеты???)"""

	i=os.dup(ipipe)
	o=os.dup(opipe)
	os.dup2(i, 3)
	os.dup2(o, 4)

	# TODO Абстрактизировать вызов интерпретатора для работы
	# в других ОС.
	interpreter = INTERPRETER
	os.system("{} -m zencad --mainonly --tgtpath {}".format(interpreter, tgtpath))

@traced
def start_unbound_application(*args, tgtpath, **kwargs):
	"""Основная процедура запуска.

	Создаёт в отдельном процессе графическую оболочку,
	После чего создаёт в своём процессе виджет, который встраивается в графическую оболочку.
	Для коммуникации между процессами создаётся pipe"""

	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	ipipe = os.pipe()
	opipe = os.pipe()

	proc = multiprocessing.Process(
		target = start_application, 
		args=(opipe[0], ipipe[1], tgtpath))
	proc.start()

	os.close(ipipe[1])
	os.close(opipe[0])

	common_unbouded_proc(pipes=(ipipe[0], opipe[1]), need_prescale=True, *args, **kwargs)

@traced
def start_worker(ipipe, opipe, path, sleeped=False, need_prescale=False, session_id=0):
	"""Создать новый поток и отправить запрос на добавление
	его вместо предыдущего ??? 

	TODO: Дополнить коментарий с подробным описанием механизма."""

	i=os.dup(ipipe)
	o=os.dup(opipe)
	os.dup2(i, 3)
	os.dup2(o, 4)

	MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(ipipe=ipipe, opipe=opipe)
	MAIN_COMMUNICATOR.send({"cmd":"clientpid", "pid":int(os.getpid())})
	
	prescale = "--prescale" if need_prescale else ""
	sleeped = "--sleeped" if sleeped else ""
	interpreter = INTERPRETER

	#cmd = "python3 /home/mirmik/.local/lib/python3.6/site-packages/zencad-0.16.2-py3.6.egg/zencad/__main__.py {path} --replace {prescale} --session_id {session_id}".format(
	#	path=path, 
	#	prescale=prescale, 
	#	session_id=session_id)

	os.system("{interpreter} -m zencad {path} --replace {prescale} {sleeped} --session_id {session_id}".format(
		interpreter=interpreter, 
		path=path, 
		prescale=prescale, 
		sleeped=sleeped,
		session_id=session_id))
	
	#saved_argv = sys.argv
	#sys.argv = cmd.split()
	#print(sys.argv)
	#runpy.run_path(path, run_name="__main__")
	#sys.argv = saved_argv # restore sys.argv

@traced
def spawn_sleeped_client(session_id):
	return start_unbounded_worker("", session_id, False, True)


@traced
def start_unbounded_worker(path, session_id, need_prescale=False, sleeped=False):
	"""Запустить процесс, обсчитывающий файл path и 
	вернуть его коммуникатор."""

	apipe = os.pipe()
	bpipe = os.pipe()

	apipe = (os.dup(apipe[0]), os.dup(apipe[1]))
	bpipe = (os.dup(bpipe[0]), os.dup(bpipe[1]))

	proc = multiprocessing.Process(target = start_worker, args=(apipe[0], bpipe[1], path, sleeped, need_prescale, session_id))
	proc.start()

	communicator = zencad.gui.communicator.Communicator(
		ipipe=bpipe[0], opipe=apipe[1])

	communicator.procpid = proc.pid

	return communicator

@traced
def update_unbound_application(*args, **kwargs):
	ipipe = 3#int(os.environ["ZENCAD_IPIPE"])
	opipe = 4#int(os.environ["ZENCAD_OPIPE"])

	common_unbouded_proc(pipes=(ipipe, opipe), *args, **kwargs)

@traced
def common_unbouded_proc(scene, 
	view=None,
	animate=None, 
	close_handle=None,
	pipes=None, 
	need_prescale=False, 
	session_id=0,
	sleeped = False):
	"""Создание приложения клиента, управляющее логикой сеанса"""

	setproctitle.setproctitle("zencad")

	ANIMATE_THREAD = None
	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	app = QApplication([])
	zencad.opengl.init_opengl()

	widget = zencad.gui.viewadaptor.DisplayWidget(
		scene=scene, 
		view=scene.viewer.create_view() if view is None else view, 
		need_prescale=need_prescale)
	DISPLAY_WINID = widget

	if pipes:
		ipipe = pipes[0]
		opipe = pipes[1]

		if MAIN_COMMUNICATOR is None:
			MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(
				ipipe=ipipe, opipe=opipe)
			MAIN_COMMUNICATOR.start_listen()

		zencad.gui.viewadaptor.bind_widget_signal(
			widget, MAIN_COMMUNICATOR)

		def stop_world():
			MAIN_COMMUNICATOR.stop_listen()
			if ANIMATE_THREAD:
				ANIMATE_THREAD.finish()

			if close_handle:
				close_handle()

			trace("FINISH UNBOUNDED QTAPP : app quit on receive")
			app.quit()
			trace("app quit on receive... after")


		def receiver(data):
			data = pickle.loads(data)
			if data["cmd"] == "stopworld": 
				stop_world()
			else:
				widget.external_communication_command(data)

		MAIN_COMMUNICATOR.newdata.connect(receiver)
		MAIN_COMMUNICATOR.oposite_clossed.connect(stop_world)
		time.sleep(0.00001)
		MAIN_COMMUNICATOR.send({"cmd":"bindwin", "id":int(DISPLAY_WINID.winId()), "pid":os.getpid(), "session_id":session_id})
		MAIN_COMMUNICATOR.wait()

	if animate:
		ANIMATE_THREAD = AnimateThread(
			widget=widget, 
			updater_function=animate)  
		ANIMATE_THREAD.start()
	
		def animate_stop():
			ANIMATE_THREAD.finish()
		
		widget.widget_closed.connect(animate_stop)
		
	if close_handle:
		widget.widget_closed.connect(close_handle)

	widget.show()
	app.exec()
	trace("FINISH UNBOUNDED QTAPP")