import threading
import os
import sys
import zencad
import signal

from zencad.util import print_to_stderr

__RETRANSLER_TRACE__ = True

class console_retransler(threading.Thread):
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
			
		os.kill(self.pid, signal.SIGKILL)

	def do_retrans(self, old=1, new=3):
		os.dup2(old, new)
		r, w = os.pipe()
		self.r = r
		self.w = w
		self.old = old
		self.new = new
		os.close(old)
		os.dup2(w, old)

		sys.stdout = os.fdopen(old, "w", 1)
