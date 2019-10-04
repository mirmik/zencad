#!/usr/bin/env python3

import os
import io
import base64
import pickle
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os 
import signal

class Communicator(QObject):

	class Listener(QThread):
		oposite_clossed = pyqtSignal()
		newdata = pyqtSignal(bytes)
		def __init__(self, ipipe):
			super().__init__()
			#self.lock = threading.RLock()
			#self.condition = threading.Condition(self.lock)
			self.event = threading.Event()
			self.pid = os.getpid()
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

				if inputdata == self.unwait_token:
					self.unwait()
					continue

				if len(inputdata) == 0:
					self.oposite_clossed.emit()
					return

				ddd = base64.decodestring(bytes(inputdata, "utf-8"))

				dddd = pickle.loads(ddd)
				if dddd["cmd"] == "tobuffer":
					self.buffer = dddd["data"]
					continue

				self.newdata.emit(ddd)

	def __init__(self, ipipe, opipe):
		super().__init__()
		self.procpid = None
		self.ipipe = ipipe
		self.opipe = opipe
		self.listener_thr = self.Listener(ipipe)
		self.newdata = self.listener_thr.newdata
		self.oposite_clossed = self.listener_thr.oposite_clossed

	def naive_connect(self, handle):
		pass

	def start_listen(self):
		self.listener_thr.start()

	def stop_listen(self):
		try:
			os.close(self.ipipe)
		except:
			pass
			#print("Warn: os.close(self.ipipe) is fault")

		try:
			os.close(self.opipe)
		except:
			pass
			#print("Warn: os.close(self.opipe) is fault")

		self.listener_thr.event.set()

		#os.kill(self.listener_thr.pid, signal.SIGKILL)
		#print("wait")
		#self.listener_thr.wait()
		#print("unwait")

	def send(self, obj):
		#print("send", obj)
		sendstr = base64.b64encode(pickle.dumps(obj)) + bytes("\n", 'utf-8')
		try:
			os.write(self.opipe, sendstr)
		except Exception as ex:
			self.stop_listen()
			#print("Warn: communicator send error", obj, ex)
		#os.flush(self.opipe)

	def wait(self):
		self.listener_thr.event.wait()
		self.listener_thr.event.clear()

	def unwait(self):
		self.send("unwait")

	def unwait_local(self):
		self.listener_thr.event.unwait()
	
	def kill(self):
		if self.procpid:
			os.kill(self.procpid, signal.SIGKILL)

	def rpc_buffer(self):
		return self.listener_thr.buffer




class NoQtCommunicator:

	class Listener(threading.Thread):
		def __init__(self, ipipe):
			super().__init__()
			#self.lock = threading.RLock()
			#self.condition = threading.Condition(self.lock)
			self.event = threading.Event()
			self.ipipe = ipipe
			self.file = io.BytesIO()
			self.stop_token = False
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
				if self.stop_token:
					return

				try:
					inputdata = readFile.readline()
				except:
					print("readFile.readline() fault")
					self.oposite_clossed.emit()
					return

				if self.stop_token:
					return

				if inputdata == self.unwait_token:
					self.unwait()
					continue

				if len(inputdata) == 0:
					self.oposite_clossed.emit()
					return

				ddd = base64.decodestring(bytes(inputdata, "utf-8"))
				self.newdata(ddd)

	def __init__(self, ipipe):
		super().__init__()
		self.ipipe = os.dup(ipipe)
		self.listener_thr = self.Listener(ipipe)

	def naive_connect(self, handle):
		self.newdata = handle
		self.listener_thr.newdata = handle

	def start_listen(self):
		self.listener_thr.start()

	def stop_listen(self):
		try:
			os.close(self.ipipe)
		except:
			print("Warn: os.close(self.ipipe) is fault")
		self.listener_thr.stop_token = True

	def wait(self):
		self.listener_thr.event.wait()
		self.listener_thr.event.clear()

	def unwait(self):
		self.send("unwait")
		