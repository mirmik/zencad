import sys
import pickle
import time
from zencad.util import print_to_stderr

import zencad.gui.actions
from zencad.gui.inotifier           import InotifyThread
from zencad.gui.info_widget         import InfoWidget
from zencad.gui.screen_saver        import ScreenSaverWidget
from zencad.gui.console             import ConsoleWidget
from zencad.gui.text_editor  		import TextEditor
from zencad.gui.display_unbounded   import start_unbounded_worker

from OCC.Display.backend import load_pyqt5, load_backend
from OCC.Display.backend import get_qt_modules

#if not load_pyqt5():
#	print("pyqt5 required to run this test")
#	sys.exit()

load_backend("qt-pyqt5")
QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

class MainWindow(QtWidgets.QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
	def __init__(self, 
		title="ZenCad",
		sleeped_optimization = False
		):
		
		super().__init__()

		# Init objects
		self.console = ConsoleWidget()
		self.texteditor = TextEditor()
		self.info_widget = InfoWidget()
		self.notifier = InotifyThread(self)
		self.screen_saver = ScreenSaverWidget()

		# Init variables
		self._bind_mode = True
		self._sleeped_optimization = sleeped_optimization
		self._current_opened = None
		self._openlock = QtCore.QMutex(QtCore.QMutex.Recursive)
		self._client_communicators = {}
		self._current_client_communicator = None

		# Init Gui
		self.setWindowTitle(title)
		self.createActions()
		self.createMenus()
		self.createToolbars()
		self.init_central_widget()

		# Bind signals
		self.notifier.changed.connect(self.reopen_current)

	def init_central_widget(self):
		self.cw = QtWidgets.QWidget()
		self.cw_layout = QtWidgets.QVBoxLayout()
		self.hsplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.vsplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

		self.cw_layout.addWidget(self.hsplitter)
		self.cw_layout.addWidget(self.info_widget)
		self.cw.setLayout(self.cw_layout)

		self.hsplitter.addWidget(self.texteditor)
		self.hsplitter.addWidget(self.vsplitter)
		self.vsplitter.addWidget(self.screen_saver)
		self.vsplitter.addWidget(self.console)

		self.resize(640,480)
		self.vsplitter.setSizes([self.height()*5/8, self.height()*3/8])
		self.hsplitter.setSizes([self.width()*3/8, self.width()*5/8])

		self.cw_layout.setContentsMargins(0,0,0,0)
		self.cw_layout.setSpacing(0)
	
		self.setCentralWidget(self.cw)

	def reopen_current(self):
		print("reopen_current")
		self._openlock.lock()
		self.open(openpath=self._current_opened, update_texteditor=False)
		self.texteditor.reopen()
		self._openlock.unlock()
		print("reopen_current...ok")

	def current_opened(self):
		return self._current_opened

	def open(self, openpath, update_texteditor=True):
		print("open")
		self._openlock.lock()

		self._current_opened = openpath
		if update_texteditor:
			self.texteditor.open(openpath)

		self.notifier.clear()
		self.notifier.add_target(openpath)

		need_prescale = False

		if self._sleeped_optimization:
			print("TODO:")
		else:
			client_communicator = start_unbounded_worker(path=openpath,
				need_prescale = need_prescale, 
				size=self.vsplitter.widget(0).size())
				
		self._current_client_communicator = client_communicator
		self._client_communicators[
			client_communicator.subproc.pid] = client_communicator

		self._current_client_communicator.oposite_clossed.connect(self.delete_communicator)
		self._current_client_communicator.newdata.connect(self.new_worker_message)
		self._current_client_communicator.start_listen()

		self._openlock.unlock()
		print("open...ok")


	def new_worker_message(self, data, procpid):
		data = pickle.loads(data)
		try:
			cmd = data["cmd"]
		except:
			print("Warn: new_worker_message: message without 'cmd' field")
			return
		print(data)

		if procpid != self._current_client_communicator.subproc_pid() and data["cmd"] != "finish_screen":
			return

		# TODO: Переделать в словарь
		if cmd == "hello": print("HelloWorld")
		elif cmd == 'bindwin': self.bind_window(winid=data['id'], pid=data["pid"])
		elif cmd == 'setopened': self.set_current_opened(path=data['path'])
		elif cmd == 'clientpid': self.clientpid = data['pid']
		elif cmd == "qmarker": self.marker_handler("q", data)
		elif cmd == "wmarker": self.marker_handler("w", data)
		elif cmd == "location": self.location_update_handle(data["loc"])
		elif cmd == "keypressed": self.internal_key_pressed(data["key"])
		elif cmd == "keypressed_raw": self.internal_key_pressed_raw(data["key"], data["modifiers"], data["text"])
		elif cmd == "keyreleased_raw": self.internal_key_released_raw(data["key"], data["modifiers"])
		elif cmd == "console": self.internal_console_request(data["data"])
		elif cmd == "trackinfo": self.info_widget.set_tracking_info(data["data"])
		elif cmd == "finish_screen": self.finish_screen(data["data"][0], data["data"][1], procpid)
		elif cmd == "fault": self.open_fault()
		elif cmd == "evalcache": self.evalcache_notification(data)
		else:
			print("Warn: unrecognized command", data)

	def bind_window(self, winid, pid):
		if self._current_client_communicator.subproc_pid() != pid:
			"""Если заявленный pid отправителя не совпадает с pid текущего коммуникатора,
			то бинд уже неактуален."""
			print("Nonactual bind")
			return
		
		if not self._openlock.tryLock():
			return

		try:		
			if self._bind_mode:
				self.embeded_window = QtGui.QWindow.fromWinId(winid)
				self.embeded_window_container = QtWidgets.QWidget.createWindowContainer(
					self.embeded_window)
				self.vsplitter.replaceWidget(0, self.embeded_window_container)
				self.update()
			
			self.client_pid = pid
			self.setWindowTitle(self._current_opened)
		
			#info("window bind success")
			self.open_in_progress = False

			#self.synchronize_subprocess_state()

			#time.sleep(0.1)
			#self.update()
		except Exception as ex:
			self._openlock.unlock()
			print_to_stderr("exception on window bind", ex)
			raise ex

		#self.subprocess_finalization_do()
		self._openlock.unlock()
		print("bind_window ... ok")

	def delete_communicator(self):
		"""Вызывается по сигналу об окончании сеанса"""
		self._openlock.lock()
		
		comm = self.sender()
		comm.stop_listen()
		#
		#if comm in self.client_finalization_list:
		#	self.client_finalization_list.remove(comm)
		#
		#del self.communicator_dictionary[comm.subproc.pid]
		#
		## clean client_finalization_list from uncostistent nodes
		#for comm in self.client_finalization_list:
		#	if comm not in self.communicator_dictionary.values():
		#		self.client_finalization_list.remove(comm)

		self._openlock.unlock()
		
	def closeEvent(self, event):
		self.notifier.finish()
		self.notifier.wait()
	

def start_application(openpath=None):
	QAPP = QtWidgets.QApplication(sys.argv[1:])
	MAINWINDOW = MainWindow()

	if openpath:
		MAINWINDOW.open(openpath)

	MAINWINDOW.show()
	QAPP.exec()