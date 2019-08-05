#!/usr/bin/env python3

import os
import io
import base64
import pickle
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class Communicator(QObject):

	class Listener(QThread):
		oposite_clossed = pyqtSignal()
		newdata = pyqtSignal(bytes)
		def __init__(self, ipipe):
			super().__init__()
			self.ipipe = ipipe
			self.file = io.BytesIO()

		def run(self):
			readFile = os.fdopen(self.ipipe)
			while(True):
				inputdata = readFile.readline()
				print("inputdata:", inputdata)

				if len(inputdata) == 0:
					self.oposite_clossed.emit()
					return

				ddd = base64.decodestring(bytes(inputdata, "utf-8"))
				self.newdata.emit(ddd)

	def __init__(self, ipipe, opipe):
		super().__init__()
		self.ipipe = ipipe
		self.opipe = opipe
		self.listener_thr = self.Listener(ipipe)
		self.newdata = self.listener_thr.newdata
		self.oposite_clossed = self.listener_thr.oposite_clossed

	def start_listen(self):
		self.listener_thr.start()

	def stop_listen(self):
		os.close(self.ipipe)
		os.close(self.opipe)

	def send(self, obj):
		sendstr = base64.b64encode(pickle.dumps(obj)) + bytes("\n", 'utf-8')
		os.write(self.opipe, sendstr)
		#os.flush(self.opipe)
