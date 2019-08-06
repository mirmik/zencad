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
import os
import pickle
import runpy

from zencad.unbound.mainwindow import MainWindow

def start_main_application():
	print("START_MAIN_APPLICATION")
	app = QApplication([])
	
	zencad.opengl.init_opengl()
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + "/../industrial-robot.svg"))
	
	pal = app.palette()
	pal.setColor(QPalette.Window, QColor(160, 161, 165))
	app.setPalette(pal)
	
	client = zencad.unbound.communicator.Communicator(ipipe=3, opipe=4)
	
	mw = MainWindow(client_communicator=client)
	mw.show()
	
	#app.aboutToQuit.connect(lambda: client.send({"cmd":"stopworld"}))
	
	app.exec()


def start_application(ipipe, opipe):
	i=os.dup(ipipe)
	o=os.dup(opipe)
	os.dup2(i, 3)
	os.dup2(o, 4)

	#os.environ["ZENCAD_MODE"] = "MAINONLY"

	#os.execve("/usr/bin/python3", ["/usr/bin/python3", "-m", "zencad"], os.environ)
	
	interpreter = "/usr/bin/python3"
	os.system("{} -m zencad --mainonly".format(interpreter))


def start_unbound_application(scene):
	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	print("START_UNBOUND_APPLICATION")

	ipipe = os.pipe()
	opipe = os.pipe()

	proc = multiprocessing.Process(target = start_application, args=(opipe[0], ipipe[1]))
	proc.start()

	os.close(ipipe[1])
	os.close(opipe[0])

	common_unbouded_proc(ipipe[0], opipe[1], scene)


def start_worker(ipipe, opipe, path):
	i=os.dup(ipipe)
	o=os.dup(opipe)
	print("dup2:", os.dup2(i, 3))
	print("dup2:", os.dup2(o, 4))

	MAIN_COMMUNICATOR = zencad.unbound.communicator.Communicator(ipipe=ipipe, opipe=opipe)
	MAIN_COMMUNICATOR.send({"cmd":"clientpid", "pid":int(os.getpid())})

	#os.environ["ZENCAD_IPIPE"] = str(3)
	#os.environ["ZENCAD_OPIPE"] = str(4)
	#os.environ["ZENCAD_MODE"] = "REPLACE_WINDOW"

	#os.execve("/usr/bin/python3", ["/usr/bin/python3", "-m", "zencad", path], os.environ)
	interpreter = "/usr/bin/python3"
	os.system("{} -m zencad --replace {}".format(interpreter, path))

def start_unbounded_worker(path):
	print("START_UNBOUNDED_WORKER")
	
	apipe = os.pipe()
	bpipe = os.pipe()

	apipe = (os.dup(apipe[0]), os.dup(apipe[1]))
	bpipe = (os.dup(bpipe[0]), os.dup(bpipe[1]))

	#print(ipipe)
	#print(opipe)

	#os.dup2(ipipe[0], 3)
	#os.dup2(ipipe[1], 5)
	#os.dup2(opipe[0], 4)
	#os.dup2(opipe[1], 6)

	#print(ipipe)
	#print(opipe)

	proc = multiprocessing.Process(target = start_worker, args=(apipe[0], bpipe[1], path))
	proc.start()

#	os.close(ipipe[1])
#	os.close(opipe[0])

	communicator = zencad.unbound.communicator.Communicator(ipipe=bpipe[0], opipe=apipe[1])

	return communicator

def update_unbound_application(scene):
	print("UPDATE_UNBOUND_APPLICATION")
	
	ipipe = 3#int(os.environ["ZENCAD_IPIPE"])
	opipe = 4#int(os.environ["ZENCAD_OPIPE"])

	print(ipipe, opipe)

	common_unbouded_proc(ipipe, opipe, scene)


def common_unbouded_proc(ipipe, opipe, scene):
	print("COMMON_UNBOUNDED_PROC")
	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	app = QApplication([])
	zencad.opengl.init_opengl()

	MAIN_COMMUNICATOR = zencad.unbound.communicator.Communicator(ipipe=ipipe, opipe=opipe)
	MAIN_COMMUNICATOR.start_listen()

	def receiver(data):
		data = pickle.loads(data)
		print("client:", data)
		if data["cmd"] == "stopworld": 
			MAIN_COMMUNICATOR.stop_listen()
			app.quit()

	MAIN_COMMUNICATOR.newdata.connect(receiver)

	DISPLAY_WINID=zencad.viewadaptor.DisplayWidget(scene, view=scene.viewer.create_view())

	#MAIN_COMMUNICATOR.send({"cmd":"hello"})
	MAIN_COMMUNICATOR.send({"cmd":"bindwin", "id":int(DISPLAY_WINID.winId())})
	#MAIN_COMMUNICATOR.send({"cmd":"clientpid", "pid":int(os.getpid())})
	MAIN_COMMUNICATOR.wait()

	DISPLAY_WINID.show()

	app.exec()
