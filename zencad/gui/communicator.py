#!/usr/bin/env python3

import os
import sys
import io
import base64
import json
import threading
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os 
import signal
from zencad.util import print_to_stderr

COMMUNICATOR_TRACE = False

class Communicator(QObject):
	smooth_stop = pyqtSignal()
	oposite_clossed = pyqtSignal()

	class Listener(QThread):
		newdata = pyqtSignal(dict, int)
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
			
			while(True):
				try:
					inputdata = self.ifile.readline()

				except Exception as ex:
					print_to_stderr("read error: error on read", ex)
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return
				
				if len(inputdata) == 0:
					self.parent._stop_listen_nowait()
					self.parent.oposite_clossed.emit()
					return

				checks = 0

				try:
					data_unpickled = json.loads(inputdata)
				except:
					print_to_stderr("warning: decode pickle:", inputdata)
					continue

				if COMMUNICATOR_TRACE:
					print_to_stderr("recv", data_unpickled)

				if data_unpickled == "unwait":
					self.unwait()
					continue

				#elif data_unpickled["cmd"] == "smooth_stopworld":
				#	self.parent.smooth_stop.emit()
				#	continue

				if data_unpickled["cmd"] == "set_opposite_pid":
					self.parent.declared_opposite_pid = data_unpickled["data"]
					continue
				
				else:
					self.newdata.emit(data_unpickled, self.parent.subproc_pid())

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

	def simple_read(self):		
		inputdata = self.ifile.readline()
		return inputdata

	def bind_handler(self, function):
		self.newdata.connect(function)

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
					pass
				except (OSError, ValueError) as ex:
					trace(ex)
	
				try:
					pass
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
		if COMMUNICATOR_TRACE:
			print_to_stderr("send", obj)

		if not self.no_communicator_pickle:
			sendstr = json.dumps(obj) + "\n"
			#sendstr = sendstr_bytes.decode("utf-8")
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
	
	def rpc_buffer(self):
		return self.listener_thr.buffer

	def set_opposite_pid(self, pid):
		self.declared_opposite_pid = pid
