#!/usr/bin/env python3

import PyQt5.QtCore as QtCore
import select
import io
import os
import signal
import fcntl

from zencad.frame.util import print_to_stderr

class Listener(QtCore.QThread):
	newdata = QtCore.pyqtSignal(str)

	def __init__(self, file, parent=None):
		super().__init__(parent)
		self._file= file		
		self._stop_token = False
		self.stream_handler = None

	def stop(self):
		self._stop_token = True

	def run(self):
		flags = fcntl.fcntl(self._file.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self._file.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

		while True:
			if self._stop_token:
				return

			res = select.select([self._file.fileno()],[self._file.fileno()],[self._file.fileno()], 0.3)
			if (len(res[0]) == 0 and len(res[1])== 0 and len(res[2])== 0):
				continue

			while True:
				data = self._file.readline()
				if len(data) == 0:
					break
				self.newdata.emit(data)

				if self.stream_handler:
					self.stream_handler(data)

if __name__ == "__main__":
	APP = QtCore.QCoreApplication([])

	def hanler(a,b):
		exit()
		APP.quit()
	
	signal.signal(signal.SIGINT, hanler)

	r, w = os.pipe()
	r_file = os.fdopen(r, "r")
	w_file = os.fdopen(w, "w")

	thr = Listener(r_file)

	thr.start()

	def stop():
		thr.stop()

	def h(data):
		print("newdata", repr(data))

	def do():
		w_file.write("afsdfasdfasf\r\n 2afdasdfasdfasdf\r\n")
		w_file.flush()

	thr.newdata.connect(h)

	timer0 = QtCore.QTimer()
	timer0.start(500)  # You may change this if you wish.
	timer0.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

	timer1 = QtCore.QTimer()
	timer1.start(1000)
	timer1.timeout.connect(do) 

	timer2 = QtCore.QTimer()
	timer2.start(5000)
	timer2.timeout.connect(stop) 

	while True: pass
	#APP.exec()