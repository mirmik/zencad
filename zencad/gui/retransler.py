import threading
import os
import sys
import zencad
import signal
import psutil
import zencad.gui.signal_os

from zencad.util import print_to_stderr
from threading import Timer

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

__RETRANSLER_TRACE__ = False

def run_with_timeout(timeout, default, f, *args, **kwargs):
	if not timeout:
		return f(*args, **kwargs)
	try:
		timeout_timer = Timer(timeout, threading.interrupt_main)
		timeout_timer.start()
		result = f(*args, **kwargs)
		return result
	except KeyboardInterrupt:
		return default
	finally:
		timeout_timer.cancel()

class console_retransler(QThread):
	def __init__(self):
		super().__init__()
		self.name = "console_retransler"
		self.do_retrans()
		self.stop_token = False

	def run(self):
		try:
			self.pid = os.getpid()
			self.readFile = os.fdopen(self.r)
		except Exception as ex:
			sys.stderr.write("console_retransler::rdopen error: ", ex, self.ipipe)
			sys.stderr.write("\r\n")
			sys.stderr.flush()
			exit(0)
		
		while(True):
			if self.stop_token:
				if __RETRANSLER_TRACE__:
					print_to_stderr("finish console retransler... ok")
				return
			try:
				inputdata = self.readFile.readline()
			except:
				if __RETRANSLER_TRACE__:
					print_to_stderr("finish console retransler... except")
				return
			
			zencad.gui.application.MAIN_COMMUNICATOR.send({"cmd":"console","data":inputdata})

	def finish(self):
		if __RETRANSLER_TRACE__:
			print_to_stderr("finish console retransler... started")
			
		#os.kill(self.pid, signal.SIGKILL)
		self.stop_token = True


		# TODO: CHANGE FINISH MODEL

		#try:
		#	os.close(self.readFile.fileno())
		#except:
		#	pass
#
		#if __RETRANSLER_TRACE__:
		#	print_to_stderr("L")
		#try:
		#	#	print_to_stderr("B")
		#	#time.sleep(0.05)
		#	zencad.gui.signal_os.kill(self.pid, zencad.gui.signal_os.sigkill)
		#except Exception as ex:
		#	print_to_stderr("console_retransler on kill", ex)
#
		#if __RETRANSLER_TRACE__:
		#	print_to_stderr("finish console retransler... exit")


		#gone, alive = psutil.wait_procs(procs, timeout=3, callback=on_terminate)
		#for p in alive:
		#    p.kill()

	def do_retrans(self, old=1, new=3):
		if __RETRANSLER_TRACE__:
			print_to_stderr("do_retrans old:{} new:{}".format(old, new))

		os.dup2(old, new)
		r, w = os.pipe()
		self.r = r
		self.w = w
		self.old = old
		self.new = new
		os.close(old)
		os.dup2(w, old)

		sys.stdout = os.fdopen(old, "w", 1)
