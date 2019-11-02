import os
import time
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class InotifyThread(QThread):
	changed = pyqtSignal()

	def __init__(self, parent):
		QThread.__init__(self, parent)
		self.lock = threading.Lock()
		self.emit_time = time.time()

	def retarget(self, path):
		self.lock.acquire()

		self.path = path
		self.last_mtime = os.stat(self.path).st_mtime

		if not self.isRunning():
			self.start()

		self.lock.release()

	def run(self):
		while 1:
			self.lock.acquire()

			try:
				if (os.stat(self.path).st_mtime != self.last_mtime):
					if time.time() - self.emit_time > 0.75:
						self.last_mtime = os.stat(self.path).st_mtime
						self.changed.emit()
						self.emit_time = time.time()
			except FileNotFoundError:
				pass

			self.lock.release()
			time.sleep(0.0001)

