# coding: utf-8

import zencad
import zencad.viewadaptor
import zencad.lazifier 
import pyservoce
import evalcache
from pyservoce import Scene, View, Viewer, Color

import tempfile
import sys
import os
import signal
import psutil

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PIL import Image
import numpy as np

import re
import time
import threading
import zencad.opengl

import runpy
import inotify.adapters
import math

import zencad.texteditor

text_editor = "subl"
main_window = None
started_by = None
edited = None
diag = None
ensave = None
desave = None
onplace = None

ABOUT_TEXT = "CAD system for righteous zen programmers."
BANNER_TEXT = (#"\n"
			"███████╗███████╗███╗   ██╗ ██████╗ █████╗ ██████╗ \n"
			"╚══███╔╝██╔════╝████╗  ██║██╔════╝██╔══██╗██╔══██╗\n"
			"  ███╔╝ █████╗  ██╔██╗ ██║██║     ███████║██║  ██║\n"
			" ███╔╝  ██╔══╝  ██║╚██╗██║██║     ██╔══██║██║  ██║\n"
			"███████╗███████╗██║ ╚████║╚██████╗██║  ██║██████╔╝\n"
			"╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ")

QMARKER_MESSAGE = "Press 'Q' to set marker"
WMARKER_MESSAGE = "Press 'W' to set marker"
DISTANCE_DEFAULT_MESSAGE = "Distance between markers"
RAWSTDOUT = None
FUTURE = None
SUBPROCESPID = None
__INVOKER__ = None
__ZENCAD_EVENT_DEBUG__ = False

def kill_subprocess():
	os.kill(SUBPROCESPID, signal.SIGTERM)

def show_label(lbl, en):
	if (en):
		lbl.setHidden(False)
	else:
		lbl.setHidden(True)

#class TextEditor(QPlainTextEdit):
#	def __init__(self):
#		QPlainTextEdit.__init__(self)
#
#	def save(self):
#		try:
#			f = open(edited, "w")
#		except IOError as e:
#			print("cannot open {} for write: {}".format(edited, e))
#		f.write(self.toPlainText())
#		f.close()
#
#	def update_text_field(self):
#		filetext = open(started_by).read()
#		self.setPlainText(filetext)
#
#	def keyPressEvent(self, event):
#		if event.key() == Qt.Key_S and QApplication.keyboardModifiers() == Qt.ControlModifier:
#			self.save()
#
#		QPlainTextEdit.keyPressEvent(self, event)

class ConsoleWidget(QTextEdit):
	append_signal = pyqtSignal(str)
	def __init__(self):
		self.stdout = sys.stdout
		sys.stdout = self

		QTextEdit.__init__(self)
		pallete = self.palette();
		pallete.setColor(QPalette.Base, QColor(30,30,30));
		pallete.setColor(QPalette.Text, QColor(255,255,255));
		self.setPalette(pallete);

		self.cursor = self.textCursor();
		self.setReadOnly(True)
		#self.fork.newdata.connect(self.append)
		
		font = QFont();
		font.setFamily("Monospace")
		font.setPointSize(10)
		font.setStyleHint(QFont.Monospace)
		self.setFont(font)

		metrics = QFontMetrics(font);
		self.setTabStopWidth(metrics.width("    "))

		self.append_signal.connect(self.append, Qt.QueuedConnection)

	def write_native(self, data):
		self.stdout.write(data)
		self.stdout.flush()
			
	def flush(self):
		self.stdout.flush()

	def write(self, data):
		self.append_signal.emit(data)
		self.write_native(data)

	def append(self, data):
		self.cursor.insertText(data)
		self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class InotifyThread(QThread):
	filechanged = pyqtSignal(str)

	def __init__(self, parent):
		QThread.__init__(self, parent)

	def init_notifier(self, path):
		self.notifier = inotify.adapters.Inotify()
		self.notifier.add_watch(path)
		self.path = path
		self.restart = True

		if not self.isRunning():
			self.start()

	def run(self):
		self.restart = False
		
		try:
			while 1:
				for event in self.notifier.event_gen():
					if event is not None:
						if 'IN_CLOSE_WRITE' in event[1]:
							print("widget: {} was rewriten. rerun initial.".format(self.path))
							self.rerun()
					if self.restart:
						self.restart = False
						break
		except Exception as e:
			print("Warning: Rerun thread was finished:", e)

	def rerun(self):
		self.filechanged.emit(self.path)

class MainWidget(QMainWindow):
	internal_rerun_signal = pyqtSignal()
	external_rerun_signal = pyqtSignal()
	animate_finish = pyqtSignal()

	def __init__(self, dispw, showconsole, showeditor, eventdebug = False):
		QMainWindow.__init__(self)
		self.eventdebug = eventdebug
		self.laststartpath=None
		self.animate_thread = None
		#self.setMouseTracking(True)
		self.rescale_on_finish=False
		self.thr=None
		self.full_screen_mode = False

		self.cw = QWidget()
		self.dispw = dispw
		self.layout = QVBoxLayout()
		self.cpannellay = QHBoxLayout()
		self.infolay = QHBoxLayout()

		self.lastopened = None
		self.setWindowTitle("zenwidget");
		#self.setWindowIcon(QIcon(":/industrial-robot.svg"));

		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0,0,0,0)

		self.texteditor = zencad.texteditor.TextEditor()
		
		self.dispw.sizePolicy().setHorizontalStretch(1)
		self.texteditor.sizePolicy().setHorizontalStretch(1) 

		self.console = ConsoleWidget()
		
		self.hsplitter = QSplitter(Qt.Horizontal)
		self.vsplitter = QSplitter(Qt.Vertical)
		self.hsplitter.addWidget(self.texteditor)
		self.vsplitter.addWidget(self.dispw)
		self.vsplitter.addWidget(self.console)
		self.hsplitter.addWidget(self.vsplitter)

		self.poslbl = QLabel("Tracking disabled")
		self.poslbl.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.poslbl.setAlignment(Qt.AlignCenter)

		self.marker1Label = QLabel(QMARKER_MESSAGE)
		self.marker1Label.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.marker1Label.setStyleSheet("QLabel { background-color : rgb(100,0,0); color : white; }");
		self.marker1Label.setAlignment(Qt.AlignCenter)

		self.marker2Label = QLabel(WMARKER_MESSAGE)
		self.marker2Label.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.marker2Label.setStyleSheet("QLabel { background-color : rgb(0,100,0); color : white; }");
		self.marker2Label.setAlignment(Qt.AlignCenter)

		self.markerDistLabel = QLabel(DISTANCE_DEFAULT_MESSAGE)
		self.markerDistLabel.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.markerDistLabel.setAlignment(Qt.AlignCenter)

		self.infoLabel = QLabel("")
		self.infoLabel.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.infoLabel.setAlignment(Qt.AlignCenter)
		show_label(self.infoLabel, False)

		self.infolay.addWidget(self.poslbl)
		self.infolay.addWidget(self.marker1Label)
		self.infolay.addWidget(self.marker2Label)
		self.infolay.addWidget(self.markerDistLabel)
		self.infolay.addWidget(self.infoLabel)

		self.layout.addLayout(self.cpannellay)
		self.layout.addWidget(self.hsplitter)
		self.layout.addLayout(self.infolay)
		self.cw.setLayout(self.layout)

		self.setCentralWidget(self.cw)

		self.createActions();
		self.createMenus();
		self.createToolbars();

		self.inotifier = InotifyThread(self)
		self.inotifier.filechanged.connect(self.rerun_current)

		self.dispw.intersectPointSignal.connect(self.poslblSlot)
		self.internal_rerun_signal.connect(self.rerun_context_invoke)

		if showeditor == False:
			self.disableEditor()

	def rerun_label_on_slot(self):
		self.infoLabel.setText("Please wait... Мы тут работаем, понимаешь.")
		show_label(self.marker1Label,False)
		show_label(self.marker2Label,False)
		show_label(self.markerDistLabel,False)
		show_label(self.poslbl,False)
		show_label(self.infoLabel,True)
		self.repaint()
		
	def rerun_label_off_slot(self):
		show_label(self.marker1Label,True)
		show_label(self.marker2Label,True)
		show_label(self.markerDistLabel,True)
		show_label(self.poslbl,True)
		show_label(self.infoLabel,False)
		self.update()

	def enableEditor(self):
		self.texteditor.setEnabled(False)

	def disableEditor(self):
		self.texteditor.setEnabled(False)
		
	def poslblSlot(self, obj):
		if obj[1]:
			self.poslbl.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(obj[0].x, obj[0].y, obj[0].z))
		else:
			self.poslbl.setText("")
			self.update()

	def create_action(self, text, action, tip, shortcut = None, checkbox = False):
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

	def createActions(self):
		self.mOpenAction = 	self.create_action("Open", 				self.openAction, 				"Open", 										"Ctrl+O")
		self.mSaveAction = 	self.create_action("Save", 				self.saveAction, 				"Open", 										)#TODO:CTRL+S
		self.mTEAction = 	self.create_action("Open in Editor", 	self.externalTextEditorOpen, 	"Editor", 										"Ctrl+E")
		self.mExitAction = 	self.create_action("Exit", 				self.close, 					"Exit", 										"Ctrl+Q")
		self.mStlExport = 	self.create_action("Export STL...", 	self.exportStlAction, 			"Export file with external STL-Mesh format")
		self.mToFreeCad= 	self.create_action("To FreeCad", 		self.to_freecad_action, 		"Save temporary BRep representation and save FreeCad script to clipboard to load it")
		self.mBrepExport = 	self.create_action("Export BREP...", 	self.exportBrepAction, 			"Export file in BREP format")
		self.mScreen = 		self.create_action("Screenshot...", 	self.screenshotAction, 			"Do screen...")
		self.mAboutAction = self.create_action("About", 			self.aboutAction, 				"About the application")
		self.mReset = 		self.create_action("Reset", 			self.resetAction, 				"Reset")
		self.mCentering = 	self.create_action("Centering", 		self.centeringAction, 			"Centering")
		self.mAutoscale = 	self.create_action("Autoscale", 		self.autoscaleAction, 			"Autoscale", 									"Ctrl+A")
		self.mOrient1 = 	self.create_action("Axinometric view", 	self.orient1, 					"Orient1")
		self.mOrient2 = 	self.create_action("Free rotation view",self.orient2, 					"Orient2")
		self.mTracking = 	self.create_action("Tracking", 			self.trackingAction, 			"Tracking",				checkbox=True)
		self.mTestAction = 	self.create_action("TestAction", 		self.testAction, 				"TestAction")
		self.mInvalCache = 	self.create_action("Invalidate cache", 	self.invalidateCacheAction, 	"Invalidate cache")
		self.mCacheInfo = 	self.create_action("Cache info", 		self.cacheInfoAction, 			"Cache info")
		self.mFinishSub = 	self.create_action("Finish subprocess", self.finishSubProcess, 			"Finish subprocess")
		self.mDebugInfo = 	self.create_action("Debug info", 		self.debugInfoAction, 			"Debug info")
		self.mHideConsole =	self.create_action("Hide console", 		self.hideConsole, 				"Hide console",				checkbox=True)
		self.mHideEditor = 	self.create_action("Hide editor", 		self.hideEditor, 				"Hide editor",				checkbox=True)
		self.mFullScreen = 	self.create_action("Full screen", 		self.fullScreen, 				"Full screen",									"F11")
		self.mWebManual = 	self.create_action("Manual online", 	self.openWebManual, 			"Open manual online")
		#self.mDisplayFullScreen = 	self.create_action("Display full screen",self.displayFullScreen, 				"Display full screen",									"F12")
		
	def set_hide(self, showeditor, showconsole):
		self.texteditor.setHidden(not showeditor)
		self.console.setHidden(not showconsole)
		self.mHideConsole.setChecked(self.console.isHidden())
		self.mHideEditor.setChecked(self.texteditor.isHidden())

	def _add_open_action(self, menu, name, path):
		def callback():
			self._open_routine(path)

		menu.addAction(self.create_action(name, callback, path))

	def _init_example_menu(self, menu, directory):
		files = os.listdir(directory)
		scripts = [f for f in files if os.path.splitext(f)[1] == ".py"]
		dirs = [f for f in files if os.path.isdir(os.path.join(directory, f)) and f != "__pycache__" and f != "fonts"]
		
		for f in sorted(scripts):
			self._add_open_action(menu, f, os.path.join(directory, f))

		for d in sorted(dirs):
			m = menu.addMenu(d)
			self._init_example_menu(m, os.path.join(directory, d))	

	def createMenus(self):
		self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.mFileMenu.addAction(self.mOpenAction)
		self.mFileMenu.addAction(self.mSaveAction)
		self.exampleMenu = self.mFileMenu.addMenu("Examples")
		self.mFileMenu.addAction(self.mStlExport)
		self.mFileMenu.addAction(self.mBrepExport)
		self.mFileMenu.addAction(self.mToFreeCad)
		self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)

		moduledir = os.path.dirname(__file__)
		self._init_example_menu(self.exampleMenu, os.path.join(moduledir, "examples"))
	
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
		self.mUtilityMenu.addAction(self.mFinishSub)

		self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
		#self.mViewMenu.addAction(self.mDisplayFullScreen)
		self.mViewMenu.addAction(self.mFullScreen)
		self.mViewMenu.addAction(self.mHideEditor)
		self.mViewMenu.addAction(self.mHideConsole)

		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.mHelpMenu.addAction(self.mAboutAction)
		self.mHelpMenu.addAction(self.mWebManual)

		#self.mHelpMenu = self.menuBar().addMenu(self.tr("&Devel"))
		#self.mHelpMenu.addAction(self.mTestAction)
		#self.mHelpMenu.addAction(self.mDebugInfo)
	
	def createToolbars(self):
		pass

	def to_freecad_action(self):
		tmpfl = tempfile.mktemp(".brep")
		print(tmpfl)
		cb = QApplication.clipboard()
		cb.clear(mode=cb.Clipboard )
		cb.setText('import Part; export = Part.Shape(); export.read("{}"); Part.show(export); Gui.activeDocument().activeView().viewAxonometric(); Gui.SendMsgToActiveView("ViewFit")'.format(tmpfl), mode=cb.Clipboard)
		pyservoce.brep_write(self.dispw.scene[0].shape(), tmpfl)
		QMessageBox.information(self, self.tr("ToFreeCad"),
			self.tr("Script copied to clipboard"));		

	def hideConsole(self, en):
		self.console.setHidden(en)

	def hideEditor(self, en):
		self.texteditor.setEnabled(not en)
		self.texteditor.setHidden(en)

	def openWebManual(self):
		QDesktopServices.openUrl(QUrl("https://mirmik.github.io/zencad", QUrl.TolerantMode));

	def exportStlAction(self):
		d, okPressed = QInputDialog.getDouble(self, "Get double","Value:", 0.01, 0, 10, 10)
		if not okPressed:
			return

		filters = "*.stl;;*.*";
		defaultFilter = "*.stl";

		path = QFileDialog.getSaveFileName(self, "STL Export", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]

		pyservoce.make_stl(self.dispw.scene[0].shape(), path, d)

	def trackingAction(self, en):
		if en:
			self.dispw.nointersect = False
		else:
			self.dispw.nointersect = True
			self.poslbl.setText("Tracking disabled")

	def externalTextEditorOpen(self):
		os.system(text_editor + " " + started_by)

	def finishSubProcess(self):
		kill_subprocess()

	def testAction(self):
		pass

	def debugInfoAction(self):
		msgBox = QMessageBox(self)
		msgBox.setWindowTitle("Debug Info")
		msgBox.setWindowModality(Qt.WindowModal);
		msgBox.setInformativeText(
			"start_by: {}"
			.format(
				started_by
			))
		msgBox.exec();

	def exportBrepAction(self):
		filters = "*.brep;;*.*";
		defaultFilter = "*.brep";

		path = QFileDialog.getSaveFileName(self, "BREP Export", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]

		pyservoce.brep_write(self.dispw.scene[0].shape(), path)

	def autoscaleAction(self):
		self.dispw.view.fit_all(0.2)

	def centeringAction(self):
		self.dispw.view.centering()

	def orient1(self):
		self.dispw.reset_orient1()

	def orient2(self):
		self.dispw.reset_orient2()

	def resetAction(self):
		self.dispw.psi =   math.cos(math.pi / 4)
		self.dispw.phi = - math.cos(math.pi / 4)
		self.dispw.view.autoscale()
		self.orient1()
		self.dispw.set_orient1()
		self.dispw.view.redraw()

	def invalidateCacheAction(self):
		files = zencad.lazy.cache.keys()
		for f in zencad.lazy.cache.keys():
			del zencad.lazy.cache[f]
		print("Invalidate cache: %d files removed" % len(files))

	def implFullScreen(self, mw, wd):
		if mw == False and self.isFullScreen():
			self.showNormal()
		if wd == False and self.isFullScreen():
			#self.vsplitter.insertWidget(0, self.dispw)
			self.setCentralWidget(self.cw)
			self.showNormal()
		if mw == True:
			self.showFullScreen()
		if wd == True:
			self.setCentralWidget(self.dispw)
			self.showFullScreen()

		self.dispw.view.redraw()
		

	def fullScreen(self):
		self.implFullScreen(not self.isFullScreen(), False)

	def displayFullScreen(self):
		#pass
		self.implFullScreen(False, not self.isFullScreen())

	def cacheInfoAction(self):
		def get_size(start_path = '.'):
			total_size = 0
			for dirpath, dirnames, filenames in os.walk(start_path):
				for f in filenames:
					fp = os.path.join(dirpath, f)
					total_size += os.path.getsize(fp)
			return total_size

		def sizeof_fmt(num, suffix='B'):
			for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
				if abs(num) < 1024.0:
					return "%3.1f%s%s" % (num, unit, suffix)
				num /= 1024.0
			return "%.1f%s%s" % (num, 'Yi', suffix)

		msgBox = QMessageBox(self)
		msgBox.setWindowTitle("Cache Info")
		msgBox.setWindowModality(Qt.WindowModal);
		msgBox.setInformativeText(
			"Path: {}"
			"<p>Hashing algorithm: {}"
			"<p>Files: {}"
			"<p>Size: {}".format(
				zencad.lazifier.cachepath,
				zencad.lazy.algo().name,
				len(zencad.lazy.cache.keys()),
				sizeof_fmt(get_size(zencad.lazifier.cachepath))
			))
		msgBox.exec();

	
	def updateDistLabel(self):
		qx,qy,qz = self.dispw.marker1[0].x, self.dispw.marker1[0].y, self.dispw.marker1[0].z
		wx,wy,wz = self.dispw.marker2[0].x, self.dispw.marker2[0].y, self.dispw.marker2[0].z
		xx,yy,zz = wx-qx, wy-qy, wz-qz
		dist = math.sqrt(xx**2 + yy**2 + zz**2)
		if self.dispw.marker1[1] or self.dispw.marker2[1]:
			self.markerDistLabel.setText("Distance: {:8.3f}".format(dist))
		else:
			self.markerDistLabel.setText(DISTANCE_DEFAULT_MESSAGE)	

	def screenshotAction(self):
		filters = "*.png;;*.bmp;;*.jpg;;*.*";
		defaultFilter = "*.png";

		path = QFileDialog.getSaveFileName(self, "Dump image", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]
		
		w = self.dispw.width()
		h = self.dispw.height()

		raw = self.dispw.view.rawarray(w,h)
		npixels = np.reshape(np.asarray(raw), (h,w,3))
		nnnpixels = np.flip(npixels, 0).reshape((w * h * 3))

		rawiter = iter(nnnpixels)
		pixels = list(zip(rawiter, rawiter, rawiter))
		
		image = Image.new("RGB", (w, h))
		image.putdata(pixels)

		image.save(path)

	def _open_routine(self, path):
		#Проверяем, чтобы в файле был хоть намек на zencad...
		#А то чего его открывать.
		global started_by
		filetext = open(path).read()
		repattern1 = re.compile(r"import *zencad|from *zencad *import")
		
		zencad_search = repattern1.search(filetext)
		print("widget: try open {}".format(path))

		#edited = path
		if zencad_search is not None:
		#	self.rerun_label_on_slot()
		#	if self.lastopened != path:
		#		self.rescale_on_finish = True
			if self.lastopened != path:
				self.rescale_on_finish=True

			self.lastopened = path
			self.inotifier.init_notifier(path)
			started_by = path
		#	os.chdir(os.path.dirname(path))
		#	self.external_rerun_signal.emit()

		zencad.showapi.mode = "update_shower"
		class runner(QThread):
			rerun_signal = pyqtSignal()
			rerun_finish_signal = pyqtSignal()
			def run(self):
				globals()["__THREAD__"] = self
				print("subthread: run")
				zencad.lazifier.restore_default_lazyopts()
				zencad.showapi.default_scene = Scene()
				zencad.showapi.mode = "update_scene"
				os.chdir(os.path.dirname(path))
				sys.path.insert(0, os.path.dirname(path))

				try:
					runpy.run_path(path, run_name="__main__")
				except Exception as e:
					print("subthread: failed with exception")
					print(e) 

				print("subthread: finish")
				self.rerun_finish_signal.emit()

		if self.thr is not None and self.thr.isRunning():
			print("subthread: interrupt")
			self.thr.terminate()


		if self.animate_thread is not None: 
			print("info: animate_thread terminate")
			self.animate_finish.emit()
			time.sleep(0.01)
			self.animate_thread = None

		self.thr = runner()
		self.thr.rerun_signal.connect(self.rerun_context_invoke)
		self.thr.rerun_finish_signal.connect(self.rerun_label_off_slot)

		self.rerun_label_on_slot()
		self.thr.start()

		self.texteditor.open(path)


	def rerun_current(self):
		self._open_routine(started_by)

	def openAction(self):
		filters = "*.py;;*.*";
		defaultFilter = "*.py";

		startpath = QDir.currentPath() if self.lastopened == None else os.path.dirname(self.lastopened)
		
		if self.lastopened is not None and os.path.normpath(zencad.exampledir) in os.path.normpath(self.lastopened):
			startpath = self.laststartpath
		else:
			self.laststartpath = startpath

		path = QFileDialog.getOpenFileName(self, "Open File", 
			startpath,
			filters, defaultFilter)

		if path[0] == '':
			return

		self._open_routine(path[0])


	def saveAction(self):
		self.texteditor.save()

	def aboutAction(self):
		QMessageBox.about(self, self.tr("About ZenCad Shower"),
			("<p>Widget for display zencad geometry."
			"<pre>{}\n"
			"{}\n"
			"Based on OpenCascade geometric core.<pre/>"
			"<p><h3>Feedback</h3>"
			"<pre>email: mirmikns@yandex.ru\n"
			"github: https://github.com/mirmik/zencad\n"
			"2018-2019<pre/>".format(BANNER_TEXT, ABOUT_TEXT)));

	def rerun_context_invoke(self):

		#print("HERE")
		#time.sleep(1)

		self.dispw.viewer.clean_context()
		self.dispw.viewer.set_triedron_axes()
		self.dispw.viewer.add_scene(self.rerun_scene)
		self.dispw.scene = self.rerun_scene
		if self.rescale_on_finish:
			self.rescale_on_finish = False
			self.resetAction()
		else:
			self.dispw.view.redraw()

		if self.rerun_animate != None:
			start_animate_thread(self.rerun_animate)
		
	def rerun_context(self, scn):
		self.rerun_scene = scn
		self.internal_rerun_signal.emit()


class update_loop(QThread):
	after_update_signal = pyqtSignal()

	def __init__(self, parent, updater_function, pause_time=0.01):
		QThread.__init__(self, parent)
		self.updater_function = updater_function 
		self.parent = parent
		self.parent.animate_thread = self
		self.wdg = parent.dispw
		self.pause_time = pause_time
		self.cancelled = False

	def finish(self):
		self.cancelled = True

	def run(self):
		while 1:
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

				mutex = QMutex()
				self.wdg.animate_updated.clear()
				self.after_update_signal.emit()
				if self.cancelled:
					mutex.unlock()
					return				
				self.wdg.animate_updated.wait()
				mutex.unlock()
				
				if self.cancelled:
					return

				time.sleep(0.01)

def show_impl(scene, animate=None, pause_time=0.01, nointersect=True, showmarkers=True, showconsole=False, showeditor=False):
	global started_by, edited
	global main_window
	started_by = sys.argv[0] if os.path.basename(sys.argv[0]) != "zencad" else os.path.join(zencad.moduledir, "__main__.py")
	edited = started_by

	app = QApplication(sys.argv)
	pal = app.palette();
	pal.setColor(QPalette.Window, QColor(160,161,165));
	app.setPalette(pal);
	
	app.lastWindowClosed.connect(sys.exit)

	app.setWindowIcon(QIcon(os.path.dirname(__file__) + '/industrial-robot.svg'))

	zencad.opengl.init_opengl()

	disp = zencad.viewadaptor.DisplayWidget(scene, nointersect, showmarkers)
	main_window = MainWidget(disp, showconsole=showconsole, showeditor=showeditor, eventdebug=__ZENCAD_EVENT_DEBUG__);	
	disp.mw = main_window
	main_window.resize(800,600)
	main_window.hsplitter.setSizes([370,500])

	main_window.texteditor.open(edited)
	main_window.inotifier.init_notifier(started_by)
	main_window.move(QApplication.desktop().screen().rect().center() - main_window.rect().center())
	main_window.show()
	main_window.set_hide(showconsole, showeditor)
	main_window.laststartpath=QDir.currentPath()

	main_window.lastopened=started_by
	
	if animate != None:
		start_animate_thread(animate)
		
	return app.exec()

#def update_show(scene, animate = None, pause_time = 0.01, nointersect=True, showmarkers=True, showconsole=False, showeditor=False):
#	if animate != None:
#		raise Exception("Animate is not supported in subprocess. You should execute this script from terminal.") 
#	globals()["ZENCAD_return_scene"] = (scene.shapes_array(), scene.color_array())
	#main_window.rerun_context(scene)
#	pass

def start_animate_thread(animate):
	thr = update_loop(main_window, animate)
	main_window.animate_thread = thr
	main_window.animate_finish.connect(thr.finish)
	thr.after_update_signal.connect(main_window.dispw.redraw)
	thr.start()


def update_scene(scene, animate=None, *args, **kwargs):
	main_window.rerun_scene = scene
	main_window.rerun_animate = animate
	globals()["__THREAD__"].rerun_signal.emit()