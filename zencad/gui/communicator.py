#!/usr/bin/env python3

import os
import sys
import io
import base64
import pickle
import threading

from zencad.util import print_to_stderr

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os 
import signal

import zencad.configure

def trace(*args):
	if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
		print_to_stderr("Communicator:", *args)

class Communicator(QObject):
	smooth_stop = pyqtSignal()

	class Listener(QThread):
		oposite_clossed = pyqtSignal()
		newdata = pyqtSignal(bytes)
		def __init__(self, ipipe, parent):
			super().__init__()
			#self.name = "Listener"
			self.parent = parent
			#self.lock = threading.RLock()
			#self.condition = threading.Condition(self.lock)
			self.event = threading.Event()
			self.pid = os.getpid()
			self.ipipe = ipipe
			self.file = io.BytesIO()
			#self.unwait_token = str(base64.b64encode(pickle.dumps("unwait")), "utf-8") + "\n"

		def unwait(self):
			self.event.set()

		def run(self):
			try:
				readFile = os.fdopen(self.ipipe)
			except Exception as ex:
				print_to_stderr("rdopen error: ", ex, self.ipipe)
				self.parent.stop_listen_nowait()
				return
			
			while(True):
				try:
					inputdata = readFile.readline()
				except:
					print_to_stderr("readFile.readline() fault")
					self.parent.stop_listen_nowait()
					#self.oposite_clossed.emit()
					return
				
				if len(inputdata) == 0:
					self.parent.stop_listen_nowait()
					#self.oposite_clossed.emit()
					return

				try:
					ddd = base64.b64decode(bytes(inputdata, "utf-8"))
				except:
					print_to_stderr("Unpicling(A):", len(inputdata), inputdata)
					self.parent.stop_listen_nowait()
					return

				try:
					dddd = pickle.loads(ddd)
				except:
					print_to_stderr("Unpicling(B):", ddd)
					self.parent.stop_listen_nowait()
					return

				if dddd == "unwait":
					self.unwait()
					continue

				#if dddd["cmd"] == "tobuffer":
				#	self.buffer = dddd["data"]
				#	continue

				if dddd["cmd"] == "smooth_stopworld":
					self.parent.smooth_stop.emit()
					continue

				if dddd["cmd"] == "set_opposite_pid":
					self.parent.procpid = dddd["data"]
					continue


				if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
					strform = str(dddd)
					if len(strform) > 100: strform = strform[0:101]
					print_to_stderr("received {}: {}".format(self.parent.procpid, strform))

				self.newdata.emit(ddd)

	def __init__(self, ipipe, opipe):
		super().__init__()
		self.procpid = None
		self.subproc = None
		self.ipipe = ipipe
		self.opipe = opipe
		self.listener_thr = self.Listener(ipipe, self)
		self.newdata = self.listener_thr.newdata
		self.oposite_clossed = self.listener_thr.oposite_clossed
		self.listen_started = False

		self.send({"cmd":"set_opposite_pid", "data":os.getpid()})

	def naive_connect(self, handle):
		pass

	def start_listen(self):
		if self.listen_started:
			pass
		else:
			self.listen_started = True
			self.listener_thr.start()

	def stop_listen(self):
		trace("stop_listen")
		
		if sys.platform == "win32" or sys.platform == "win64": 
			return

		try:
			trace("close ipipe")
			os.close(self.ipipe)
		except:
			pass
			#print_to_stderr("Warn: os.close(self.ipipe) is fault")
#
		try:
			trace("close opipe")
			os.close(self.opipe)
		except:
			pass
			#print_to_stderr("Warn: os.close(self.opipe) is fault")

		trace("event set")
		self.listener_thr.event.set()
		
		#print(sys.platform)
		trace("wait listener")
		self.listener_thr.wait()

		#os.kill(self.listener_thr.pid, signal.SIGKILL)
		#print("wait")
		#self.listener_thr.wait()
		#print("unwait")

	def stop_listen_nowait(self):
		trace("stop_listen_nowait")
		try:
			os.close(self.ipipe)
		except:
			pass
#
		try:
			os.close(self.opipe)
		except:
			pass

	def send(self, obj):
		if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
			strobj = str(obj)
			if len(strobj) > 100: strobj=strobj[:101]
			print_to_stderr("communucator send to {}: {}".format(self.procpid, strobj))
		sendstr = base64.b64encode(pickle.dumps(obj)) + bytes("\n", 'utf-8')
		try:
			os.write(self.opipe, sendstr)
			if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
				print_to_stderr("Correct sending")
			return True
		except Exception as ex:
			if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
				print_to_stderr("Exception on send", self.procpid, strobj, ex)
			self.stop_listen()
			return False
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
		trace("kill")
		#if self.procpid:
		#	os.kill(self.procpid, signal.SIGKILL)
		try:
			if self.subproc:
				self.subproc.terminate()
		except:
			pass

	def rpc_buffer(self):
		return self.listener_thr.buffer

	def set_opposite_pid(self, pid):
		self.procpid = pid



#class NoQtCommunicator:
#
#	class Listener(threading.Thread):
#		def __init__(self, ipipe):
#			super().__init__()
#			#self.lock = threading.RLock()
#			#self.condition = threading.Condition(self.lock)
#			self.event = threading.Event()
#			self.ipipe = ipipe
#			self.file = io.BytesIO()
#			self.stop_token = False
#			self.unwait_token = str(base64.b64encode(pickle.dumps("unwait")), "utf-8") + "\n"
#
#		def unwait(self):
#			self.event.set()
#
#		def run(self):
#			try:
#				readFile = os.fdopen(self.ipipe)
#			except Exception as ex:
#				print_to_stderr("rdopen error: ", ex, self.ipipe)
#				exit(0)
#			
#			while(True):
#				if self.stop_token:
#					return
#
#				try:
#					inputdata = readFile.readline()
#				except:
#					print("readFile.readline() fault")
#					self.oposite_clossed.emit()
#					return
#
#				if self.stop_token:
#					return
#
#				if inputdata == self.unwait_token:
#					self.unwait()
#					continue
#
#				if len(inputdata) == 0:
#					self.oposite_clossed.emit()
#					return
#
#				ddd = base64.decodestring(bytes(inputdata, "utf-8"))
#				self.newdata(ddd)
#
#	def __init__(self, ipipe):
#		super().__init__()
#		self.ipipe = os.dup(ipipe)
#		self.listener_thr = self.Listener(ipipe)
#
#	def naive_connect(self, handle):
#		self.newdata = handle
#		self.listener_thr.newdata = handle
#
#	def start_listen(self):
#		self.listener_thr.start()
#
#	def stop_listen(self):
#		try:
#			os.close(self.ipipe)
#		except:
#			print("Warn: os.close(self.ipipe) is fault")
#		self.listener_thr.stop_token = True
#
#	def wait(self):
#		self.listener_thr.event.wait()
#		self.listener_thr.event.clear()
#
#	def unwait(self):
#		self.send("unwait")
#		#