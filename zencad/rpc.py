#!/usr/bin/env python3

import os
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CommandTranslator(QObject):
	class Listener(QThread):
		newdata = pyqtSignal(bytes)

		def __init__(self, parent, r):
			QThread.__init__(self, parent)
			self.r = r

		def run(self):
			while 1:
				data = os.read(self.r, 512)
				self.newdata.emit(data)

	def __init__(self, r, w):
		QObject.__init__(self)
		self.r = r
		self.w = w
		self.listener = self.Listener(self, self.r)
		self.listener.start()

	def send(self, cmd, args):
		os.write(self.w, pickle.dumps({"cmd":cmd, "args":args}))

	def stop(self):
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

	def __init__(self, r, w):
		CommandTranslator.__init__(self, r, w)
		self.listener.newdata.connect(self.parse)
		self.hashtable = {
			"screen": self.screenCommandSignal, 
			"stopworld": self.stopWorldSignal, 
		}

	def parse(self, data):
		dct = pickle.loads(data)
		cmd = dct["cmd"]
		self.hashtable[cmd].emit(*dct["args"])


