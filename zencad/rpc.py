#!/usr/bin/env python3

import os
import sys
import pickle
import threading
import random
import socket

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class Transler(QObject):
	class Listener(QThread):
		newdata = pyqtSignal(bytes)

		def __init__(self, parent, lsock):
			QObject.__init__(self, parent)
			self.lsock = lsock

		def run(self):
			try:
				while 1:
					data = self.lsock.recv(512)
					print("data recved", data)
					self.newdata.emit(data)
			except Exception as e:
				self.parent().print_error("clossed pipe detected", e)

	def __init__(self, parent, oposite=None):
		print("Transler::__init__", oposite)
		QObject.__init__(self, parent)
		
		self.rsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		self.wsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		self.callbacks = { "setoposite": self.setoposite }

		self.raddress = "/tmp/zencad-socket-" + str(random.randint(0, 9223372036854775807))
		print("create connection point", self.raddress)
		self.rsock.bind(self.raddress)
		
		if oposite is None:
			pass		
		else:
			print("connect to oposite", oposite)
			self.waddress=oposite
			self.wsock.connect(oposite) 
			self.send("setoposite", (self.raddress,))
			
		self.listener = self.Listener(self, self.rsock)
		self.listener.newdata.connect(self.parse)
		self.listener.start()

	def setoposite(self, oposite):
		self.waddress=oposite
		self.wsock.connect(oposite) 

	def get_apino(self):
		return self.raddress

	def send(self, cmd, args):
		print("send", cmd, args)
		self.wsock.send(pickle.dumps({"cmd":cmd, "args":args}))

	def parse(self, data):
		dct = pickle.loads(data)
		cmd = dct["cmd"]
		if not cmd in self.callbacks:
			print("unregistred command", cmd)
		else:
			self.callbacks[cmd](*dct["args"])

	def stop(self):
		self.rsock.close()
		self.wsock.close()
		self.listener.quit()

class ClientTransler(Transler):
	screen_signal = 	pyqtSignal(str)
	stopworld_signal = 		pyqtSignal()
	centering_signal = pyqtSignal()
	autoscale_signal = pyqtSignal()
	reset_signal = 	pyqtSignal()

	def __init__(self, parent, oposite=None):
		Transler.__init__(self, parent, oposite)

		self.callbacks["stopworld"] = lambda: self.stopworld_signal.emit()

class ServerTransler(Transler):
	pass		