#!/usr/bin/env python3

import os
import sys
import io
import base64
import pickle
import threading
import traceback

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
	oposite_clossed = pyqtSignal()

	class Listener(QThread):
		newdata = pyqtSignal(bytes, int)
		def __init__(self, ifile, parent):
			super().__init__()
			self.parent = parent
			self.event = threading.Event()
			self.pid = os.getpid()
			self.ifile = ifile
			#self.file = io.BytesIO()

		def unwait(self):
			self.event.set()

		def run(self):
			checks = 0
			oposite_pid = lambda : self.parent.subproc_pid()
			trace("START LISTEN")

			try:
				trace("COMMUNICATOR: ifile:{}".format(self.ifile))
				readFile = self.ifile
			except Exception as ex:
				trace("rdopen error: (oposite:{}, ifile:{})".format(oposite_pid(), self.ifile), ex, self.ifile)
				self.parent.stop_listen_nowait()
				return
			
			while(True):
				try:
					inputdata = readFile.readline()

					if zencad.configure.CONFIGURE_PRINT_COMMUNICATION_DUMP:
						print_to_stderr(f"Receive: sender:{oposite_pid()} len:{len(inputdata)} dump50:{repr(inputdata[:50])}")

				except Exception as ex:
					trace("readFile.readline() fault (oposite:{}, ifile:{})".format(oposite_pid(), self.ifile), ex)
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return
				
				if len(inputdata) == 0:
					checks += 1
					if checks < 3:
						continue
					trace("input data zero size (oposite:{}, ifile:{})".format(oposite_pid(), self.ifile))
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return

				checks = 0

				try:
					data_base64 = base64.b64decode(bytes(inputdata, "utf-8"))
				except:
					trace("Unpicling(A):", len(inputdata), inputdata)
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return

				try:
					data_unpickled = pickle.loads(data_base64)
				except:
					trace("Unpicling(B):", data_base64)

					#DEBUG
					continue

					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return

				if zencad.configure.CONFIGURE_PRINT_COMMUNICATION_DUMP:
					print_to_stderr(f"Receive: sender:{oposite_pid()} unpickle:{data_unpickled}")

				if data_unpickled == "unwait":
					self.unwait()
					continue

				if data_unpickled["cmd"] == "smooth_stopworld":
					self.parent.smooth_stop.emit()
					continue

				if data_unpickled["cmd"] == "set_opposite_pid":
					self.parent.declared_opposite_pid = data_unpickled["data"]
					continue


				if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
					strform = str(data_unpickled)
					if len(strform) > 100: strform = strform[0:101]
					print_to_stderr("received {}: {}".format(self.parent.subproc_pid(), strform))
				
				self.newdata.emit(data_base64, self.parent.subproc_pid())

	def __init__(self, ifile, ofile):
		super().__init__()
		self.declared_opposite_pid = None
		self.subproc = None
		self.ifile = ifile
		self.ofile = ofile
		self.listener_thr = self.Listener(ifile=ifile, parent=self)
		self.newdata = self.listener_thr.newdata
		self.listen_started = False
		self.closed = False
		self.closed_fds = False

		self.send({"cmd":"set_opposite_pid", "data":os.getpid()})

	def naive_connect(self, handle):
		pass

	def start_listen(self):
		if self.listen_started:
			pass
		else:
			self.listen_started = True
			self.listener_thr.start()

	def subproc_pid(self):
		""" PID процесса на той стороне можно узнать двумя путями.
		Либо это pid связанный с объектом subprocess, связанным с ним, 
		либо, если этот объект отсутствует, можно воспользоваться
		переданной кем-либо информацией о таком процессе. 
		Иногда процедура возвращает None. Это значит, что процесс на той стороне не был создан
		через subprocess и никто не успел уведомить коммуникатор о его pid."""
		return self.subproc.pid if self.subproc else self.declared_opposite_pid

	def close_pipes(self):
		if self.subproc is not None:
			self.subproc.stdin.close()
			self.subproc.stdout.close()

		else:
			if not self.closed_fds:
				try:
					#trace("close ifile", self.ifile.fileno(), self.subproc_pid())
					pass
					#self.ifile.close()
				except (OSError, ValueError) as ex:
					trace(ex)
	
				try:
					#trace("close ofile", self.ofile.fileno(), self.subproc_pid())
					pass
					#self.ofile.close()
				except (OSError, ValueError) as ex:
					trace(ex)

	def stop_listen(self):
		trace("stop_listen", self.subproc.pid if self.subproc else None)

		if self.closed:
			return
		
		#if sys.platform == "win32" or sys.platform == "win64": 
			# WHAT???? TODO: Расследовать, почему так и прокоментировать
		#	return

		self.close_pipes()

		trace("event set")
		self.listener_thr.event.set()
		
		#trace("wait listener")
		#self.listener_thr.wait()

		self.closed_fds = True
		self.closed = True

	def _stop_listen_nowait(self):
		trace("stop_listen_nowait", self.subproc.pid if self.subproc else None)

		if self.closed:
			return
		
		self.close_pipes()

		self.closed_fds = True
		self.closed = True

	def send(self, obj):
		if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
			strobj = str(obj)
			if len(strobj) > 100: strobj=strobj[:101]
			print_to_stderr("communicator send to {}: {}".format(self.subproc_pid(), strobj))
		sendstr_bytes = base64.b64encode(pickle.dumps(obj)) + b"\n"
		sendstr = sendstr_bytes.decode("utf-8")
		try:
			self.ofile.write(sendstr)
			self.ofile.flush()

			if zencad.configure.CONFIGURE_PRINT_COMMUNICATION_DUMP:
				print_to_stderr(f"Send: pipe:{self.ofile} recver:{self.subproc_pid()} len:{len(sendstr)} dump50:{[sendstr[:50]]}")
				print_to_stderr(f"Send: pipe:{self.ofile} recver:{self.subproc_pid()} unpickle:{obj}")

			return True
		except Exception as ex:
			if zencad.configure.CONFIGURE_COMMUNICATOR_TRACE:
				print_to_stderr(f"Exception on send: op_pid:{self.subproc_pid()} ifile:{self.ifile}, ofile:{self.ofile}, {strobj}, {ex}")
				traceback.print_exc()
			self.stop_listen()
			return False
			#print("Warn: communicator send error", obj, ex)
		#os.flush(self.ofile)

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
		self.declared_opposite_pid = pid



#class NoQtCommunicator:
#
#	class Listener(threading.Thread):
#		def __init__(self, ifile):
#			super().__init__()
#			#self.lock = threading.RLock()
#			#self.condition = threading.Condition(self.lock)
#			self.event = threading.Event()
#			self.ifile = ifile
#			self.file = io.BytesIO()
#			self.stop_token = False
#			self.unwait_token = str(base64.b64encode(pickle.dumps("unwait")), "utf-8") + "\n"
#
#		def unwait(self):
#			self.event.set()
#
#		def run(self):
#			try:
#				readFile = os.fdopen(self.ifile)
#			except Exception as ex:
#				print_to_stderr("rdopen error: ", ex, self.ifile)
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
#				data_base64 = base64.decodestring(bytes(inputdata, "utf-8"))
#				self.newdata(data_base64)
#
#	def __init__(self, ifile):
#		super().__init__()
#		self.ifile = os.dup(ifile)
#		self.listener_thr = self.Listener(ifile)
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
#			os.close(self.ifile)
#		except:
#			print("Warn: os.close(self.ifile) is fault")
#		self.listener_thr.stop_token = True
#
#	def wait(self):
#		self.listener_thr.event.wait()
#		self.listener_thr.event.clear()
#
#	def unwait(self):
#		self.send("unwait")
#		#