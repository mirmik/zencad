#!/usr/bin/env python3

import os
import pickle
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class NoQtTransler:
	@staticmethod
	def listener_func(owner, r):
		try:
			while 1:
				data = os.read(r, 512)
				owner.parse(data)
		except:
			print("closed pipe detected")
			print("???? TODO")

	def __init__(self, r, w):
		self.r = r
		self.w = w
		self.listener = threading.Thread(target=self.listener_func, args=(self, self.r,))
		self.listener.start()

		self.hashtable = {}

	def parse(self, data):
		print("NoQtTransler::parse")
		dct = pickle.loads(data)
		cmd = dct["cmd"]
		self.hashtable[cmd].emit(*dct["args"])

	def send(self, cmd, args):
		print("NoQtTransler::send")
		os.write(self.w, pickle.dumps({"cmd":cmd, "args":args}))	

class CommandTranslator(QObject):
	class Listener(QThread):
		newdata = pyqtSignal(bytes)

		def __init__(self, parent, r):
			QThread.__init__(self, parent)
			self.r = r

		def run(self):
			try:
				while 1:
					data = os.read(self.r, 512)
					self.newdata.emit(data)
			except:
				print("closed pipe detected")
				print("???? TODO")

	def __init__(self, r, w):
		QObject.__init__(self)
		self.r = r
		self.w = w
		self.listener = self.Listener(self, self.r)
		self.listener.start()

	def send(self, cmd, args):
		os.write(self.w, pickle.dumps({"cmd":cmd, "args":args}))

	def stop(self):
		os.close(self.r)
		os.close(self.w)
		self.listener.quit()

class ApplicationNode(CommandTranslator):
	def __init__(self, r, w):
		CommandTranslator.__init__(self, r, w)
		self.listener.newdata.connect(self.parse)

	def parse(self, data):
		print("ApplicationNode::parse", data)
		pass

class EvaluatorNode(CommandTranslator):
	screenCommandSignal = pyqtSignal(str)
	stopWorldSignal = pyqtSignal()
	actionCenteringSignal = pyqtSignal()
	actionAutoscaleSignal = pyqtSignal()
	actionResetSignal = pyqtSignal()

	def __init__(self, r, w):
		CommandTranslator.__init__(self, r, w)
		self.listener.newdata.connect(self.parse)
		self.hashtable = {
			"screen": self.screenCommandSignal, 
			"stopworld": self.stopWorldSignal, 
			"centering": self.actionCenteringSignal, 
			"autoscale": self.actionAutoscaleSignal, 
			"resetview": self.actionResetSignal, 
		}

	def parse(self, data):
		dct = pickle.loads(data)
		cmd = dct["cmd"]
		self.hashtable[cmd].emit(*dct["args"])


