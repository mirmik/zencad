#!/usr/bin/env python3

import os
import sys
import io
import base64
import pickle
import threading
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os 
import signal
from zencad.util import print_to_stderr

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
			
			try:
				readFile = self.ifile
			except Exception as ex:
				self.parent.stop_listen_nowait()
				return
			
			while(True):
				try:
					inputdata = readFile.readline()

				except Exception as ex:
					print("read error: error on read", ex)
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return
				
				if len(inputdata) == 0:
					checks += 1
					if checks < 3:
						continue
					print("read error: len(inputdata)==0")
			
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return

				checks = 0

				try:
					data_base64 = base64.b64decode(bytes(inputdata, "utf-8"))
				except:
					print(f"warning: decode b64: len:{len(inputdata)}, data:{inputdata}")
					continue

				try:
					data_unpickled = pickle.loads(data_base64)
				except:
					print("warning: decode pickle:", data_base64)
					continue

				print_to_stderr("recv", data_unpickled)

				if data_unpickled == "unwait":
					self.unwait()
					continue

				if data_unpickled["cmd"] == "smooth_stopworld":
					self.parent.smooth_stop.emit()
					continue

				if data_unpickled["cmd"] == "set_opposite_pid":
					self.parent.declared_opposite_pid = data_unpickled["data"]
					continue
				
				self.newdata.emit(data_base64, self.parent.subproc_pid())

	def __init__(self, ifile, ofile, no_communicator_pickle=False):
		super().__init__()
		self.no_communicator_pickle = no_communicator_pickle
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
		if self.closed:
			return

		self.close_pipes()
		self.listener_thr.event.set()
		
		self.closed_fds = True
		self.closed = True

	def _stop_listen_nowait(self):
		if self.closed:
			return
		
		self.close_pipes()

		self.closed_fds = True
		self.closed = True

	def send(self, obj):
		print_to_stderr("send", obj)
		if not self.no_communicator_pickle:
			sendstr_bytes = base64.b64encode(pickle.dumps(obj)) + b"\n"
			sendstr = sendstr_bytes.decode("utf-8")
		else:
			sendstr = str(obj) + "\r\n"
		try:
			self.ofile.write(sendstr)
			self.ofile.flush()
			return True
		
		except Exception as ex:
			self.stop_listen()
			return False
		
	def wait(self):
		self.listener_thr.event.wait()
		self.listener_thr.event.clear()

	def unwait(self):
		self.send("unwait")

	def unwait_local(self):
		self.listener_thr.event.unwait()
	
	def kill(self):
		raise Exception("kill?")
		#trace("kill")
		#try:
		#	if self.subproc:
		#		self.subproc.terminate()
		#except:
		#	pass

	def rpc_buffer(self):
		return self.listener_thr.buffer

	def set_opposite_pid(self, pid):
		self.declared_opposite_pid = pid
