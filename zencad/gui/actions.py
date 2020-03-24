from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import tempfile
import subprocess
import signal

import zencad.gui.util
import zencad.gui.settingswdg
from zencad.gui.inotifier import InotifyThread

ABOUT_TEXT = "CAD system for righteous zen programmers."
BANNER_TEXT = (  # "\n"
	"███████╗███████╗███╗   ██╗ ██████╗ █████╗ ██████╗ \n"
	"╚══███╔╝██╔════╝████╗  ██║██╔════╝██╔══██╗██╔══██╗\n"
	"  ███╔╝ █████╗  ██╔██╗ ██║██║     ███████║██║  ██║\n"
	" ███╔╝  ██╔══╝  ██║╚██╗██║██║     ██╔══██║██║  ██║\n"
	"███████╗███████╗██║ ╚████║╚██████╗██║  ██║██████╔╝\n"
	"╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═════╝ "
)

class MainWindowActionsMixin:
	def create_action(self, text, action, tip, shortcut=None, checkbox=False, defcheck=False):
		act = QAction(self.tr(text), self)
		act.setStatusTip(self.tr(tip))

		if shortcut is not None:
			act.setShortcut(self.tr(shortcut))

		if not checkbox:
			act.triggered.connect(action)
		else:
			act.setCheckable(True)
			act.toggled.connect(action)
			act.setChecked(defcheck)

		return act

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
				"2018-2020<pre/>".format(BANNER_TEXT, ABOUT_TEXT)
			),
		)

	def navigation_reference(self):
		msgBox = QMessageBox()
		msgBox.setWindowTitle("Справка по навигации:")
		msgBox.setText(
			"LeftButton+Move или Alt+Move: Вращение камеры вокруг центра\n"
			"RightButton+Move или Shift+Move: Стрейф центра.\n"
			"F5/F6: Перемещение центра фронтально.\n"
			"PgUp/PgDown или MouseWheel: Изменение масштаба\n"
			"\n"
			"При зажатой LeftButton или скрытом текстовом редакторе:\n"
			"A : влево.\n"
			"D : вправо.\n"
			"W : вперёд.\n"
			"S : назад.\n"
			"\n"
			"Для навигации центра используйте Navigation/Visible center\n"
			"и режим перспективы Navigation/Perspective\n"
			"Режим перспективы позволяет заглядывать внутрь моделей."
		)
		msgBox.exec()
		
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
		path = zencad.gui.util.open_file_dialog(self, directory=os.path.dirname(self.current_opened))

		if path[0] == "":
			return

		self._open_routine(path[0])

	def saveAction(self):
		self.texteditor.save()

	def saveAsAction(self):
		path, template = zencad.gui.util.save_file_dialog(self)

		if path == "":
			return

		self.texteditor.save_as(path)

	def exportStlAction(self):
		self.client_communicator.send({"cmd": "exportstl"})		

	def exportBrepAction(self):
		self.client_communicator.send({"cmd": "exportbrep"})	

	def externalTextEditorOpen(self):
		cmd = zencad.settings.get_external_editor_command()
		subprocess.Popen(cmd.format(path=self.current_opened), shell=True)

	def to_freecad_action(self):
		self.client_communicator.send({"cmd": "to_freecad"})

	def screenshotAction(self):
		#TODO: Востановить алгоритм взятия скриншота с дампом view буффера.

		filters = "*.png;;*.bmp;;*.jpg;;*.*"
		defaultFilter = "*.png"

		retpath = QFileDialog.getSaveFileName(
			self, "Dump image", QDir.currentPath(), filters, defaultFilter
		)

		path = retpath[0]

		if path == "":
			return

		screen = self.screen()

		file = QFile (path)
		file.open(QIODevice.WriteOnly)
		screen.save(file, "PNG")

		#w = self.dispw.width()
		#h = self.dispw.height()

		#raw = self.dispw.view.rawarray(w, h)
		#npixels = np.reshape(np.asarray(raw), (h, w, 3))
		#nnnpixels = np.flip(npixels, 0).reshape((w * h * 3))

		#rawiter = iter(nnnpixels)
		#pixels = list(zip(rawiter, rawiter, rawiter))

		#image = Image.new("RGB", (w, h))
		#image.putdata(pixels)

		#image.save(path)

	def resetAction(self):
		self.client_communicator.send({"cmd": "resetview"})

	def centeringAction(self):
		self.client_communicator.send({"cmd": "centering"})

	def autoscaleAction(self):
		self.client_communicator.send({"cmd": "autoscale"})

	def trackingAction(self, en):
		self.client_communicator.send({"cmd": "tracking", "en": en})
		self.info_widget.set_tracking_info_status(en)

	def orient1(self):
		self.client_communicator.send({"cmd": "orient1"})

	def orient2(self):
		self.client_communicator.send({"cmd": "orient2"})

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

		self.client_communicator.send({"cmd":"keyboard_retranslate", "en": not en})

	#def testAction(self):
	#	raise NotImplementedError

	def cacheInfoAction(self):
		def get_size(start_path="."):
			total_size = 0
			for dirpath, dirnames, filenames in os.walk(start_path):
				for f in filenames:
					fp = os.path.join(dirpath, f)
					total_size += os.path.getsize(fp)
			return total_size

		def sizeof_fmt(num, suffix="B"):
			for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
				if abs(num) < 1024.0:
					return "%3.1f%s%s" % (num, unit, suffix)
				num /= 1024.0
			return "%.1f%s%s" % (num, "Yi", suffix)

		msgBox = QMessageBox(self)
		msgBox.setWindowTitle("Cache Info")
		msgBox.setWindowModality(Qt.WindowModal)
		msgBox.setInformativeText(
			"Path: {}"
			"<p>Hashing algorithm: {}"
			"<p>Files: {}"
			"<p>Size: {}".format(
				zencad.lazifier.cachepath,
				zencad.lazy.algo().name,
				len(zencad.lazy.cache.keys()),
				sizeof_fmt(get_size(zencad.lazifier.cachepath)),
			)
		)
		msgBox.exec()

	def debugInfoAction(self):
		raise NotImplementedError

	def fullScreen(self):
		#if self.presentation_mode: return
		if not self.fscreen_mode:
			self.showFullScreen()
			self.fscreen_mode = True
		else:
			self.showNormal()
			self.fscreen_mode = False

	def view_only(self, en):
		if en:	
			self.menu_bar_height = self.menuBar().height()
			#self.texteditor.setHidden(True)
			#self.console.setHidden(True)
			self.menuBar().setFixedHeight(0)
			self.info_widget.setHidden(True)
		else:
			#self.texteditor.setHidden(False)
			#self.console.setHidden(False)
			self.menuBar().setFixedHeight(self.menu_bar_height)
			self.info_widget.setHidden(False)

		self.view_mode = en

	def viewOnly(self):
		self.view_only(not self.view_mode)

	def display_mode_enable(self, en):
		if not en:
			self.hideEditor(False)
			self.hideConsole(False)
			self.mHideConsole.setChecked(False)
			self.mHideEditor.setChecked(False)			

		else:
			self.hideEditor(True)
			self.hideConsole(True)
			self.mHideConsole.setChecked(True)
			self.mHideEditor.setChecked(True)

	def displayMode(self):
		self.display_mode_enable(not (self.texteditor.isHidden() or self.console.isHidden()))		

	def coordsDifferenceMode(self, en):
		self.info_widget.coords_difference_mode = en
		self.info_widget.update_dist()

#	def reopen_current(self):
#		self._open_routine(self.current_opened)

	def settings(self):
		wdg = zencad.gui.settingswdg.SettingsWidget()
		status = wdg.exec()

		if status == 1 and zencad.configure.CONFIGURE_SLEEPED_OPTIMIZATION:
			self.remake_sleeped_thread()

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

	def _init_recent_menu(self, menu):
		def _add_open_action(menu, name, path):
			def callback():
				self._open_routine(path)

			menu.addAction(self.create_action(name, callback, path))

		for l in zencad.settings.Settings.get_recent():
			_add_open_action(menu, os.path.basename(l), l)

	def update_recent_menu(self):
		self.recentMenu.clear()
		self._init_recent_menu(self.recentMenu)

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
		self.mSaveAction = self.create_action("Save", self.saveAction, "Save", "Ctrl+S")
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
		self.mNavRefer = self.create_action(
			"Navigation reference", self.navigation_reference, "Navigation reference"
		)
		self.mSettings = self.create_action(
			"Settings", self.settings, "GUI/View Settings"
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

		self.mFirstPersonMode = self.create_action(
			"FirstPersonMode", self.first_person_mode, "First Person Mode"
		)

		self.mTracking = self.create_action(
			"Tracking", self.trackingAction, "Tracking", checkbox=True
		)

		self.mPerspective = self.create_action(
			"Perspective", self.set_perspective, "Set Perspective", checkbox=True, defcheck=zencad.settings.get(["memory","perspective"])=='true'
		)

		self.mVisCenter = self.create_action(
			"Visible center", self.set_center_visible, "Visible center", checkbox=True, defcheck=False
		)

		self.perspective_checkbox_state = zencad.settings.get(["memory","perspective"])=='true'

		#self.mTestAction = self.create_action(
		#	"TestAction", self.testAction, "TestAction"
		#)
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
		self.mAutoUpdate = self.create_action(
			"Restart on update", self.auto_update, "Restart on update", checkbox=True, defcheck=True,
		)
		self.mFullScreen = self.create_action(
			"Full screen", self.fullScreen, "Full screen", "F11"
		)
		self.mDisplayMode = self.create_action(
			"Display mode", self.displayMode, "Display mode", "F10"
		)

		self.view_mode = False
		self.mViewOnly = self.create_action(
			"Hide Bars", self.viewOnly, "Hide bars", "F9"
		)
		self.mReopenCurrent = self.create_action(
			"Reopen current", self.reopen_current, "Reopen current", "Ctrl+R"
		)
		self.mWebManual = self.create_action(
			"Online manual", zencad.gui.util.open_online_manual, "Open online manual in browser", "F1"
		)
		self.mCoordsDiff = self.create_action(
			"Coords difference",
			self.coordsDifferenceMode,
			"Coords difference mode",
			checkbox=True,
		)

	def set_center_visible(self, en):
		self.client_communicator.send({"cmd": "set_center_visible", "en": en})

	def createMenus(self):
		self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.mFileMenu.addAction(self.mReopenCurrent)
		self.mFileMenu.addAction(self.mOpenAction)
		self.mFileMenu.addAction(self.mCreateTemp)
		self.mFileMenu.addAction(self.mCreateAction)
		self.mFileMenu.addAction(self.mSaveAction)
		self.mFileMenu.addAction(self.mSaveAs)
		self.mFileMenu.addSeparator()
		self.exampleMenu = self.mFileMenu.addMenu("Examples")
		self.recentMenu = self.mFileMenu.addMenu("Recent")
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mStlExport)
		self.mFileMenu.addAction(self.mBrepExport)
		self.mFileMenu.addAction(self.mToFreeCad)
		self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)

		moduledir = os.path.dirname(__file__)
		self._init_example_menu(self.exampleMenu, os.path.join(moduledir, "../examples"))
		self._init_recent_menu(self.recentMenu)

		self.mEditMenu = self.menuBar().addMenu(self.tr("&Edit"))
		self.mEditMenu.addAction(self.mTEAction)
		self.mEditMenu.addSeparator()
		self.mEditMenu.addAction(self.mSettings)

		self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
		self.mNavigationMenu.addAction(self.mReset)
		self.mNavigationMenu.addAction(self.mCentering)
		self.mNavigationMenu.addAction(self.mAutoscale)
		self.mNavigationMenu.addAction(self.mOrient1)
		self.mNavigationMenu.addAction(self.mOrient2)
		self.mNavigationMenu.addSeparator()
		self.mNavigationMenu.addAction(self.mPerspective)
		self.mNavigationMenu.addAction(self.mVisCenter)
		self.mNavigationMenu.addAction(self.mFirstPersonMode)

		self.mUtilityMenu = self.menuBar().addMenu(self.tr("&Utility"))
		self.mUtilityMenu.addAction(self.mAutoUpdate)
		self.mUtilityMenu.addSeparator()
		self.mUtilityMenu.addAction(self.mTracking)
		self.mUtilityMenu.addAction(self.mCoordsDiff)
		self.mUtilityMenu.addSeparator()
		self.mUtilityMenu.addAction(self.mCacheInfo)
		self.mUtilityMenu.addAction(self.mInvalCache)
		# self.mUtilityMenu.addAction(self.mFinishSub)

		self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
		# self.mViewMenu.addAction(self.mDisplayFullScreen)
		self.mViewMenu.addAction(self.mFullScreen)
		self.mViewMenu.addAction(self.mDisplayMode)
		self.mViewMenu.addAction(self.mViewOnly)
		self.mViewMenu.addAction(self.mHideEditor)
		self.mViewMenu.addAction(self.mHideConsole)

		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.mHelpMenu.addAction(self.mWebManual)
		self.mHelpMenu.addAction(self.mNavRefer)
		self.mHelpMenu.addAction(self.mAboutAction)

	def createToolbars(self):
		pass

	def set_perspective(self, en):
		if self.client_communicator:
			self.client_communicator.send({"cmd": "set_perspective", "en": en})
		self.perspective_checkbox_state = en

		zencad.settings.set(["memory", "perspective"], "true" if en else "false")

	def first_person_mode(self):
		self.client_communicator.send({"cmd": "first_person_mode"})

	def auto_update(self, en):
		if not en:
			self.notifier.stop()
			self.notifier = None
		else:
			self.notifier = InotifyThread(self)
			if self.current_opened:
				self.notifier.retarget(self.current_opened)
				self.notifier.changed.connect(self.reopen_current)
				self.notifier.start()	
		