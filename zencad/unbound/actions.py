from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import tempfile
import signal
import threading

import zencad.unbound.application

ABOUT_TEXT = "CAD system for righteous zen programmers."
BANNER_TEXT = (  # "\n"
	"███████╗███████╗███╗   ██╗ ██████╗ █████╗ ██████╗ \n"
	"╚══███╔╝██╔════╝████╗  ██║██╔════╝██╔══██╗██╔══██╗\n"
	"  ███╔╝ █████╗  ██╔██╗ ██║██║     ███████║██║  ██║\n"
	" ███╔╝  ██╔══╝  ██║╚██╗██║██║     ██╔══██║██║  ██║\n"
	"███████╗███████╗██║ ╚████║╚██████╗██║  ██║██████╔╝\n"
	"╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═════╝ "
)

SETTINGS = {"external_text_editor": "subl"}

class mixin():
	def create_action(self, text, action, tip, shortcut=None, checkbox=False):
		act = QAction(self.tr(text), self)
		act.setStatusTip(self.tr(tip))

		if shortcut is not None:
			act.setShortcut(self.tr(shortcut))

		if not checkbox:
			act.triggered.connect(action)
		else:
			act.setCheckable(True)
			act.toggled.connect(action)

		return act

	def openWebManual(self):
		QDesktopServices.openUrl(
			QUrl("https://mirmik.github.io/zencad", QUrl.TolerantMode)
		)
	
	def aboutAction(self):
		QMessageBox.about(
			self,
			self.tr("About ZenCad Shower"),
			(
				"<p>Widget for display zencad geometry."
				"<pre>{}\n"
				"{}\n"
				"Based on OpenCascade geometric core.<pre/>"
				"<p><h3>Feedback</h3>"
				"<pre>email: mirmikns@yandex.ru\n"
				"github: https://github.com/mirmik/zencad\n"
				"2018-2019<pre/>".format(BANNER_TEXT, ABOUT_TEXT)
			),
		)

	def create_new_do(self, path):
		f = open(path, "w")
		f.write(
			"#!/usr/bin/env python3\n#coding: utf-8\n\nfrom zencad import *\n\nm=box(10)\ndisp(m)\n\nshow()\n"
		)
		f.close()
		self._open_routine(path)

	def createNewAction(self):
		filters = "*.py;;*.*"
		defaultFilter = "*.py"

		path = QFileDialog.getSaveFileName(
			self, "Create New File", self.laststartpath, filters, defaultFilter
		)

		if path[0] == "":
			return

		self.create_new_do(path[0])

	def createNewTemporary(self):
		tmpfl = tempfile.mktemp(".py")
		self.create_new_do(tmpfl)

	def openAction(self):
		filters = "*.py;;*.*"
		defaultFilter = "*.py"

		startpath = (
			QDir.currentPath()
			if self.current_opened is None
			else os.path.dirname(self.current_opened)
		)

		#if self.current_opened is not None and os.path.normpath(
		#	zencad.exampledir
		#) in os.path.normpath(self.lastopened):
		#	startpath = self.laststartpath
		#else:
		#	self.laststartpath = startpath

		path = QFileDialog.getOpenFileName(
			self, "Open File", startpath, filters, defaultFilter
		)

		if path[0] == "":
			return

		self._open_routine(path[0])

	def saveAction(self):
		raise NotImplementedError

	def saveAsAction(self):
		raise NotImplementedError

	def exportStlAction(self):
		raise NotImplementedError

	def exportBrepAction(self):
		raise NotImplementedError

	def externalTextEditorOpen(self):
		os.system(SETTINGS["external_text_editor"] + " " + started_by)

	def to_freecad_action(self):
		self.communicator.send({"cmd": "to_freecad"})

	def screenshotAction(self):
		raise NotImplementedError

	def resetAction(self):
		self.communicator.send({"cmd": "resetview"})

	def centeringAction(self):
		self.communicator.send({"cmd": "centering"})

	def autoscaleAction(self):
		self.communicator.send({"cmd": "autoscale"})

	def trackingAction(self, en):
		self.communicator.send({"cmd": "tracking", "en": en})

	def orient1(self):
		self.communicator.send({"cmd": "orient1"})

	def orient2(self):
		self.communicator.send({"cmd": "orient2"})

	def invalidateCacheAction(self):
		files = zencad.lazy.cache.keys()
		for f in zencad.lazy.cache.keys():
			del zencad.lazy.cache[f]
		print("Invalidate cache: %d files removed" % len(files))

	def hideConsole(self, en):
		self.console.setHidden(en)

	def hideEditor(self, en):
		self.texteditor.setEnabled(not en)
		self.texteditor.setHidden(en)

	def testAction(self):
		raise NotImplementedError

	def cacheInfoAction(self):
		raise NotImplementedError

	def debugInfoAction(self):
		raise NotImplementedError

	def fullScreen(self):
		raise NotImplementedError

	def coordsDifferenceMode(self, en):
		self.coords_difference_mode = en
		self.updateDistLabel()

	def _add_open_action(self, menu, name, path):
		def callback():
			self._open_routine(path)

		menu.addAction(self.create_action(name, callback, path))

	def _init_example_menu(self, menu, directory):
		files = os.listdir(directory)
		scripts = [f for f in files if os.path.splitext(f)[1] == ".py"]
		dirs = [
			f
			for f in files
			if os.path.isdir(os.path.join(directory, f))
			and f != "__pycache__"
			and f != "fonts"
		]

		for f in sorted(scripts):
			self._add_open_action(menu, f, os.path.join(directory, f))

		for d in sorted(dirs):
			m = menu.addMenu(d)
			self._init_example_menu(m, os.path.join(directory, d))

	def createActions(self):
		self.mCreateAction = self.create_action(
			"CreateNew...", self.createNewAction, "Create"
		)
		self.mCreateTemp = self.create_action(
			"NewTemporary", self.createNewTemporary, "CreateTemporary", "Ctrl+N"
		)
		self.mOpenAction = self.create_action(
			"Open...", self.openAction, "Open", "Ctrl+O"
		)
		self.mSaveAction = self.create_action("Save", self.saveAction, "Save")
		self.mSaveAs = self.create_action("SaveAs...", self.saveAsAction, "SaveAs...")
		self.mTEAction = self.create_action(
			"Open in Editor", self.externalTextEditorOpen, "Editor", "Ctrl+E"
		)
		self.mExitAction = self.create_action("Exit", self.close, "Exit", "Ctrl+Q")
		self.mStlExport = self.create_action(
			"Export STL...",
			self.exportStlAction,
			"Export file with external STL-Mesh format",
		)
		self.mToFreeCad = self.create_action(
			"To FreeCad",
			self.to_freecad_action,
			"Save temporary BRep representation and save FreeCad script to clipboard to load it",
		)
		self.mBrepExport = self.create_action(
			"Export BREP...", self.exportBrepAction, "Export file in BREP format"
		)
		self.mScreen = self.create_action(
			"Screenshot...", self.screenshotAction, "Do screen..."
		)
		self.mAboutAction = self.create_action(
			"About", self.aboutAction, "About the application"
		)
		self.mReset = self.create_action("Reset", self.resetAction, "Reset")
		self.mCentering = self.create_action(
			"Centering", self.centeringAction, "Centering"
		)
		self.mAutoscale = self.create_action(
			"Autoscale", self.autoscaleAction, "Autoscale", "Ctrl+A"
		)
		self.mOrient1 = self.create_action("Axinometric view", self.orient1, "Orient1")
		self.mOrient2 = self.create_action(
			"Free rotation view", self.orient2, "Orient2"
		)
		self.mTracking = self.create_action(
			"Tracking", self.trackingAction, "Tracking", checkbox=True
		)
		self.mTestAction = self.create_action(
			"TestAction", self.testAction, "TestAction"
		)
		self.mInvalCache = self.create_action(
			"Invalidate cache", self.invalidateCacheAction, "Invalidate cache"
		)
		self.mCacheInfo = self.create_action(
			"Cache info", self.cacheInfoAction, "Cache info"
		)
		# self.mFinishSub = 	self.create_action("Finish subprocess", self.finishSubProcess, 			"Finish subprocess")
		self.mDebugInfo = self.create_action(
			"Debug info", self.debugInfoAction, "Debug info"
		)
		self.mHideConsole = self.create_action(
			"Hide console", self.hideConsole, "Hide console", checkbox=True
		)
		self.mHideEditor = self.create_action(
			"Hide editor", self.hideEditor, "Hide editor", checkbox=True
		)
		self.mFullScreen = self.create_action(
			"Full screen", self.fullScreen, "Full screen", "F11"
		)
		self.mWebManual = self.create_action(
			"Online manual", self.openWebManual, "Open online manual in browser"
		)
		self.mCoordsDiff = self.create_action(
			"Coords difference",
			self.coordsDifferenceMode,
			"Coords difference mode",
			checkbox=True,
		)

	def createMenus(self):
		self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.mFileMenu.addAction(self.mCreateTemp)
		self.mFileMenu.addAction(self.mCreateAction)
		self.mFileMenu.addAction(self.mOpenAction)
		self.mFileMenu.addAction(self.mSaveAction)
		self.mFileMenu.addAction(self.mSaveAs)
		self.exampleMenu = self.mFileMenu.addMenu("Examples")
		self.mFileMenu.addAction(self.mStlExport)
		self.mFileMenu.addAction(self.mBrepExport)
		self.mFileMenu.addAction(self.mToFreeCad)
		self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)

		moduledir = os.path.dirname(__file__)
		self._init_example_menu(self.exampleMenu, os.path.join(moduledir, "../examples"))

		self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
		self.mNavigationMenu.addAction(self.mReset)
		self.mNavigationMenu.addAction(self.mCentering)
		self.mNavigationMenu.addAction(self.mAutoscale)
		self.mNavigationMenu.addAction(self.mOrient1)
		self.mNavigationMenu.addAction(self.mOrient2)
		self.mNavigationMenu.addAction(self.mTracking)

		self.mUtilityMenu = self.menuBar().addMenu(self.tr("&Utility"))
		self.mUtilityMenu.addAction(self.mTEAction)
		self.mUtilityMenu.addAction(self.mCacheInfo)
		self.mUtilityMenu.addSeparator()
		self.mUtilityMenu.addAction(self.mInvalCache)
		# self.mUtilityMenu.addAction(self.mFinishSub)

		self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
		# self.mViewMenu.addAction(self.mDisplayFullScreen)
		self.mViewMenu.addAction(self.mCoordsDiff)
		self.mViewMenu.addAction(self.mFullScreen)
		self.mViewMenu.addAction(self.mHideEditor)
		self.mViewMenu.addAction(self.mHideConsole)

		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.mHelpMenu.addAction(self.mAboutAction)
		self.mHelpMenu.addAction(self.mWebManual)

	def createToolbars(self):
		pass





	def _open_routine(self, path, initupdate=True):
		# Проверяем, чтобы в файле был хоть намек на zencad...
		# А то чего его отрисовывать.

		print("_open_routine")
#
		#global started_by
#
		self.openlock.acquire()
#
		#filetext = open(path).read()
		#repattern1 = re.compile(r"import *zencad|from *zencad *import")
#
		#zencad_search = repattern1.search(filetext)
		#print("widget: try open {}".format(path))
#
		#self.setWindowTitle(os.path.basename(path))
		#self.laststartpath = path
#
		#if zencad_search is not None:
		#	if self.lastopened != path:
		#		self.rescale_on_finish = True
#
		#	self.lastopened = path
		#	self.inotifier.init_notifier(path)
		#	started_by = path
#
		#self.texteditor.open(path)

		self.set_current_opened(path)
#
		#if initupdate:
		#	if (
		#		globals()["__THREAD__"] is not None
		#		and globals()["__THREAD__"].isRunning()
		#	):
		#		self.openlock.release()
		#		self.reopen_after_finish = True
		#		return

		#self.client_communicator.send({"cmd": "stopworld"})
		oldpid = self.clientpid

		self.client_communicator.stop_listen()
		
		self.client_communicator = zencad.unbound.application.start_unbounded_worker(path)
		self.client_communicator.start_listen()
#
		self.client_communicator.newdata.connect(self.new_worker_message)
		
		os.kill(oldpid, signal.SIGKILL)
		
		#	zencad.showapi.mode = "update_shower"
#
		#	class runner(QThread):
		#		rerun_signal = pyqtSignal()
		#		rerun_finish_signal = pyqtSignal()
#
		#		def run(self):
		#			globals()["__THREAD__"] = self
		#			print("subthread: run")
		#			self.setTerminationEnabled(True)
		#			zencad.lazifier.restore_default_lazyopts()
		#			zencad.showapi.default_scene = pyservoce.Scene()
		#			zencad.showapi.mode = "update_scene"
		#			os.chdir(os.path.dirname(path))
		#			sys.path.insert(0, os.path.dirname(path))
#
		#			try:
		#				runpy.run_path(path, run_name="__main__")
		#			except Exception as e:
		#				print("subthread: failed with exception")
		#				print(e)
#
		#			print("subthread: finish")
		#			self.rerun_finish_signal.emit()
#
		#	if self.animate_thread is not None:
		#		print("animate_thread: terminate")
		#		self.animate_finish.emit()
		#		while not self.animate_thread.isFinished():
		#			pass
		#		print("animate_thread: terminate finish")
		#		self.animate_thread = None
#
		#	self.thr = runner()
		#	self.thr.rerun_signal.connect(self.rerun_context_invoke)
		#	self.thr.rerun_finish_signal.connect(self.rerun_label_off_slot)
		#	self.thr.rerun_finish_signal.connect(self.reopen_if_need)
#
		#	self.rerun_label_on_slot()
		#	self.thr.start()
#
		self.openlock.release()
		print("_open_routine...ok")
