# coding: utf-8

import zencad
import zencad.console
import zencad.viewadaptor
import zencad.lazifier
import zencad.opengl
import zencad.texteditor

import zencad.unbound.communicator

import pyservoce
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import multiprocessing
import os
import pickle


MAIN_COMMUNICATOR = None
DISPLAY_WINID = None

class MainWindow(QMainWindow):
	def __init__(self, client_communicator):
		super().__init__()
		self.console = zencad.console.ConsoleWidget()

		self.client_communicator = client_communicator
		print("connect")
		self.client_communicator.newdata.connect(self.new_worker_message)
		self.client_communicator.start_listen()

		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)

		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(QWidget())
		self.vsplitter.addWidget(self.console)

		self.resize(800,600)
		self.setCentralWidget(self.hsplitter)

	def new_worker_message(self, data):
		data = pickle.loads(data)
		cmd = data["cmd"]

		print("MainWindow:communicator:", data)

		if cmd == "hello": print("HelloWorld")
		if cmd == 'bindwin': self.bind_window(winid=data['id'])

	def bind_window(self, winid):
		container = QWindow.fromWinId(winid)
		cc = QWidget.createWindowContainer(container)
		self.vsplitter.replaceWidget(0, cc)

def start_application(ipipe, opipe):
	app = QApplication([])
	zencad.opengl.init_opengl()

	#pal = app.palette()
	#pal.setColor(QPalette.Window, QColor(160, 161, 165))
	#app.setPalette(pal)
	client = zencad.unbound.communicator.Communicator(ipipe=ipipe, opipe=opipe)

	mw = MainWindow(client_communicator=client)
	mw.show()

	app.aboutToQuit.connect(lambda: client.send({"cmd":"stopworld"}))

	app.exec()


def start_application_unbound(scene):
	global MAIN_COMMUNICATOR
	global DISPLAY_WINID

	ipipe = os.pipe()
	opipe = os.pipe()

	proc = multiprocessing.Process(target = start_application, args=(opipe[0], ipipe[1]))
	proc.start()

	#os.close(ipipe[1])
	#os.close(opipe[0])

	MAIN_COMMUNICATOR = zencad.unbound.communicator.Communicator(ipipe=ipipe[0], opipe=opipe[1])
	MAIN_COMMUNICATOR.start_listen()

	app = QApplication([])

	def receiver(data):
		data = pickle.loads(data)
		print("client:", data)
		if data["cmd"] == "stopworld": app.quit()

	MAIN_COMMUNICATOR.newdata.connect(receiver)

	DISPLAY_WINID=zencad.viewadaptor.DisplayWidget(scene, view=scene.viewer.create_view())

	MAIN_COMMUNICATOR.send({"cmd":"hello"})
	MAIN_COMMUNICATOR.send({"cmd":"bindwin", "id":int(DISPLAY_WINID.winId())})

	DISPLAY_WINID.show()

	app.exec()