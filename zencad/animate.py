from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time

import zencad

class AnimateThread(QThread):
	after_update_signal = pyqtSignal()

	def __init__(self, widget, updater_function, animate_step=0.01):
		QThread.__init__(self)
		self.updater_function = updater_function
		#self.parent = widget
		widget.animate_thread = self
		self.wdg = widget
		self.animate_step = animate_step
		self.cancelled = False

		self.after_update_signal.connect(widget.continuous_redraw)

	def finish(self):
		self.cancelled = True
		self.wdg.animate_updated.set()

	def set_animate_step(self, step):
			self.animate_step = step

	def run(self):
		time.sleep(0.1)
		lasttime = time.time() - self.animate_step
		while 1:
			curtime = time.time()
			deltatime = curtime - lasttime

			if deltatime < self.animate_step:
				time.sleep(self.animate_step - deltatime)

			lasttime = time.time()

			ensave = zencad.lazy.encache
			desave = zencad.lazy.decache
			onplace = zencad.lazy.onplace
			diag = zencad.lazy.diag
			if self.wdg.inited:
				zencad.lazy.encache = False
				zencad.lazy.decache = False
				zencad.lazy.onplace = True
				zencad.lazy.diag = False
				self.updater_function(self.wdg)
				zencad.lazy.onplace = onplace
				zencad.lazy.encache = ensave
				zencad.lazy.decache = desave
				zencad.lazy.diag = diag

				self.wdg.animate_updated.clear()
				if self.cancelled:
					return

				self.after_update_signal.emit()
				self.wdg.animate_updated.wait()

				if self.cancelled:
					return
