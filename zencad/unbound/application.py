# coding: utf-8

import zencad

import zencad.gui.console
import zencad.gui.texteditor
import zencad.gui.viewadaptor

import zencad.lazifier
import zencad.opengl

from zencad.animate import AnimateThread
import zencad.unbound.communicator
import zencad.gui.actions

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import multiprocessing
import os
import pickle
import runpy

from zencad.gui.mainwindow import MainWindow

__TRACED__= False

def trace(s):
	if __TRACED__:
		print("APPTRACE: {}".format(s))

def traced(func):
	def decor(*argv, **kwargs):
		trace(func.__name__)
		return func(*argv, **kwargs)
	return decor

@traced
def start_main_application(tgtpath):
	"""Запустить графический интерфейс в текущем потоке.

	Используются файловые дескрипторы по умолчанию, которые длжен открыть
	вызывающий поток."""

	app = QApplication([])
	
	zencad.opengl.init_opengl()
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + "/../industrial-robot.svg"))
	
	#TODO: Настройка цветов.
	pal = app.palette()
	pal.setColor(QPalette.Window, QColor(160, 161, 165))
	app.setPalette(pal)
	
	mw = MainWindow(
		client_communicator=
			zencad.unbound.communicator.Communicator(ipipe=3, opipe=4),
		openned_path=tgtpath)

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
	interpreter = "/usr/bin/python3"
	os.system("{} -m zencad --mainonly --tgtpath {}".format(interpreter, tgtpath))

@traced
def start_unbound_application(*args, tgtpath, **kwargs):
	"""Основная процедура запуска.

	Создаёт в отдельном процессе графическую оболочку,
	После чего создаёт в своём процессе виджет, который встраивается в GUI.
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

	common_unbouded_proc(pipes=(ipipe[0], opipe[1]), *args, **kwargs)

@traced
def start_worker(ipipe, opipe, path):
	"""Создать новый поток и отправить запрос на добавление
	его вместо предыдущего ??? 

	TODO: Дополнить коментарий с подробным описанием механизма."""

	i=os.dup(ipipe)
	o=os.dup(opipe)
	os.dup2(i, 3)
	os.dup2(o, 4)

	MAIN_COMMUNICATOR = zencad.unbound.communicator.Communicator(ipipe=ipipe, opipe=opipe)
	MAIN_COMMUNICATOR.send({"cmd":"clientpid", "pid":int(os.getpid())})

	interpreter = "/usr/bin/python3"
	os.system("{} -m zencad --replace {}".format(interpreter, path))

@traced
def start_unbounded_worker(path):
	"""Запустить процесс, обсчитывающий файл path и 
	вернуть его коммуникатор."""

	apipe = os.pipe()
	bpipe = os.pipe()

	apipe = (os.dup(apipe[0]), os.dup(apipe[1]))
	bpipe = (os.dup(bpipe[0]), os.dup(bpipe[1]))

	proc = multiprocessing.Process(target = start_worker, args=(apipe[0], bpipe[1], path))
	proc.start()

	return zencad.unbound.communicator.Communicator(
		ipipe=bpipe[0], opipe=apipe[1])

@traced
def update_unbound_application(*args, **kwargs):
	ipipe = 3#int(os.environ["ZENCAD_IPIPE"])
	opipe = 4#int(os.environ["ZENCAD_OPIPE"])

	common_unbouded_proc(pipes=(ipipe, opipe), *args, **kwargs)

@traced
def common_unbouded_proc(scene, animate=None, close_handle=None, pipes=None):
	"""Создание приложения клиента, управляющее логикой сеанса"""

	ANIMATE_THREAD = None
	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	app = QApplication([])
	zencad.opengl.init_opengl()

	widget = zencad.gui.viewadaptor.DisplayWidget(
		scene, view=scene.viewer.create_view())
	DISPLAY_WINID = widget

	if pipes:
		ipipe = pipes[0]
		opipe = pipes[1]

		MAIN_COMMUNICATOR = zencad.unbound.communicator.Communicator(
			ipipe=ipipe, opipe=opipe)
		MAIN_COMMUNICATOR.start_listen()

		zencad.gui.viewadaptor.bind_widget_markers_signal(
			widget, MAIN_COMMUNICATOR)

		def receiver(data):
			data = pickle.loads(data)
			if data["cmd"] == "stopworld": 
				MAIN_COMMUNICATOR.stop_listen()
				if ANIMATE_THREAD:
					ANIMATE_THREAD.finish()

				if close_handle:
					close_handle()

				trace("FINISH UNBOUNDED QTAPP : app quit on receive")
				app.quit()
				trace("app quit on receive... after")
			else:
				widget.external_communication_command(data)

		MAIN_COMMUNICATOR.newdata.connect(receiver)
		MAIN_COMMUNICATOR.send({"cmd":"bindwin", "id":int(DISPLAY_WINID.winId())})
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