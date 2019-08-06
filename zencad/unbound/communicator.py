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
			#self.lock = threading.RLock()
			#self.condition = threading.Condition(self.lock)
			self.event = threading.Event()
			self.ipipe = ipipe
			self.file = io.BytesIO()
			self.unwait_token = str(base64.b64encode(pickle.dumps("unwait")), "utf-8") + "\n"

		def unwait(self):
			self.event.set()

		def run(self):
			try:
				readFile = os.fdopen(self.ipipe)
			except Exception as ex:
				print("rdopen error: ", ex, self.ipipe)
				exit(0)
			
			while(True):
				try:
					inputdata = readFile.readline()
				except:
					print("readFile.readline() fault")
					self.oposite_clossed.emit()
					return

				print("HERE!!!!!")
				print(inputdata)
				print(self.unwait_token)
				print("HERE!!!!!....ok")
				if inputdata == self.unwait_token:
					return self.unwait()

				if len(inputdata) == 0:
					print("len(inputdata) == 0")
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
		try:
			os.close(self.ipipe)
		except:
			print("Warn: os.close(self.ipipe) is fault")

		try:
			os.close(self.opipe)
		except:
			print("Warn: os.close(self.opipe) is fault")

	def send(self, obj):
		sendstr = base64.b64encode(pickle.dumps(obj)) + bytes("\n", 'utf-8')
		try:
			os.write(self.opipe, sendstr)
		except Exception as ex:
			self.stop_listen()
			print("Warn: communicator send error", obj, ex)
		#os.flush(self.opipe)

	def wait(self):
		print("wait")
		self.listener_thr.event.wait()
		self.listener_thr.event.clear()
		print("wait... ok")
		