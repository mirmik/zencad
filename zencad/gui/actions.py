from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import tempfile
import subprocess

import zencad.gui.util
import zencad.gui.settingswdg

from zencad.gui.defaults import SCRIPT_TEMPLATE
from zencad.settings import Settings

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
    def create_action(
        self,
        text,
        callback,
        tip,
        shortcut=None,
        checkbox=False,
        defcheck=False,
    ):
        action = QAction(self.tr(text), self)
        action.setStatusTip(self.tr(tip))
        if shortcut is not None:
            action.setShortcut(self.tr(shortcut))
        if checkbox:
            action.setCheckable(True)
            action.toggled.connect(callback)
            action.setChecked(defcheck)
        else:
            action.triggered.connect(callback)
        return action

    def create_standard_actions(self):
        self.mCreateAction = self.create_action(
            "Create New...", self.createNewAction, "Create a Python script"
        )
        self.mCreateTemp = self.create_action(
            "New Temporary", self.createNewTemporary, "Create a temporary script", "Ctrl+N"
        )
        self.mOpenAction = self.create_action(
            "Open...", self.openAction, "Open a Python script", "Ctrl+O"
        )
        self.mSaveAction = self.create_action(
            "Save", self.saveAction, "Save the current script", "Ctrl+S"
        )
        self.mSaveAs = self.create_action(
            "Save As...", self.saveAsAction, "Save the current script under a new name"
        )
        self.mTEAction = self.create_action(
            "Open in Editor",
            self.externalTextEditorOpen,
            "Open the script in an external editor",
            "Ctrl+E",
        )
        self.mExitAction = self.create_action(
            "Exit", self.close, "Exit ZenCad", "Ctrl+Q"
        )
        self.mHideConsole = self.create_action(
            "Hide console", self.hideConsole, "Hide console", checkbox=True
        )
        self.mHideEditor = self.create_action(
            "Hide editor", self.hideEditor, "Hide editor", checkbox=True
        )
        self.mAutoUpdate = self.create_action(
            "Restart on update",
            self.auto_update,
            "Reload when the script changes",
            checkbox=True,
            defcheck=True,
        )
        self.mFullScreen = self.create_action(
            "Full screen", self.fullScreen, "Toggle full screen", "F11"
        )
        self.mDisplayMode = self.create_action(
            "Display mode", self.displayMode, "Toggle editor and console", "F10"
        )
        self.mViewOnly = self.create_action(
            "Hide Bars", self.viewOnly, "Toggle menu and information bars", "F9"
        )
        self.mReopenCurrent = self.create_action(
            "Reopen current", self.reopen_current, "Reopen current", "Ctrl+R"
        )

    def add_new_create_open_standard_actions(self):
        self.mFileMenu.addAction(self.mReopenCurrent)
        self.mFileMenu.addAction(self.mOpenAction)
        self.mFileMenu.addAction(self.mCreateTemp)
        self.mFileMenu.addAction(self.mCreateAction)
        self.mFileMenu.addAction(self.mSaveAction)
        self.mFileMenu.addAction(self.mSaveAs)

    def add_exit_standard_action(self):
        self.mFileMenu.addAction(self.mExitAction)

    def add_editor_standard_action(self):
        self.mEditMenu.addAction(self.mTEAction)

    def create_new_do(self, path):
        with open(path, "w", encoding="utf-8") as output:
            output.write(SCRIPT_TEMPLATE)
        self.open(path)

    def createNewAction(self):
        current = self.current_opened()
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Create New File",
            "" if current is None else os.path.dirname(current),
            "*.py;;*.*",
            "*.py",
        )
        if path:
            self.create_new_do(path)

    def createNewTemporary(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        temporary.close()
        self.create_new_do(temporary.name)

    def openAction(self):
        current = self.current_opened()
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "" if current is None else os.path.dirname(current),
            "*.py;;*.*",
            "*.py",
        )
        if path:
            self.open(path)

    def saveAction(self):
        self.texteditor.save()

    def saveAsAction(self):
        path, _selected_filter = QFileDialog.getSaveFileName(
            self, "Save File", "", "*.py;;*.*", "*.py"
        )
        if path:
            self.texteditor.save_as(path)
            self.open(path)

    def externalTextEditorOpen(self):
        current = self.current_opened()
        if current is None:
            return
        command = Settings.get(["gui", "text_editor"])
        subprocess.Popen(command.format(path=current), shell=True)

    def hideConsole(self, hidden):
        self.console.setHidden(hidden)
        if not hidden:
            self.ensure_console_visible()

    def hideEditor(self, hidden):
        self.texteditor.setEnabled(not hidden)
        self.texteditor.setHidden(hidden)
        if hidden:
            self.display_widget.setFocus()

    def fullScreen(self):
        if self._fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self._fullscreen = not self._fullscreen

    def viewOnly(self):
        self.view_only(not self.view_mode)

    def display_mode_enable(self, enabled):
        self.mHideConsole.setChecked(enabled)
        self.mHideEditor.setChecked(enabled)
        if not enabled:
            self.texteditor.setFocus()

    def displayMode(self):
        self.display_mode_enable(
            not (self.texteditor.isHidden() or self.console.isHidden())
        )

    def auto_update(self, enabled):
        self.notifier.set_enabled(enabled)

    def _init_recent_menu(self, menu):
        for path in Settings.get_recent():
            self._add_open_action(menu, os.path.basename(path), path)

    def update_recent_menu(self):
        self.recentMenu.clear()
        self._init_recent_menu(self.recentMenu)

    def openStartEvent(self, path):
        Settings.add_recent(os.path.abspath(path))
        self.update_recent_menu()

    def _send_viewer_command(self, command):
        self.display_widget.external_communication_command(command)

    def aboutAction(self):
        QMessageBox.about(
            self,
            self.tr("About ZenCad Shower"),
            (
                "<p>Widget for displaying zencad geometry."
                "<pre>{}\n"
                "{}\n"
                "ZenCad version: {}\n"
                "Based on OpenCascade geometric core.<pre/>"
                "<p><h3>Feedback</h3>"
                "<pre>email: mirmikns@yandex.ru\n"
                "github: https://github.com/mirmik/zencad\n"
                "2018-2021<pre/>".format(
                    BANNER_TEXT,
                    ABOUT_TEXT,
                    zencad.__version__)
            ),
        )

    def navigation_reference(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Справка по навигации:")
        msgBox.setText(
            "LeftButton+Move или Alt+Move: Вращение камеры вокруг центра\n"
            "RightButton+Move или Shift+Move: Стрейф центра.\n"
            "F5/F6: Перемещение центра фронтально. (режим с активной перспективой)\n"
            "PgUp/PgDown или MouseWheel: Изменение масштаба\n"
            "\n"
            "При зажатой LeftButton или скрытом текстовом редакторе:\n"
            "A : влево.\n"
            "D : вправо.\n"
            "W : вперёд. (режим с активной перспективой)\n"
            "S : назад. (режим с активной перспективой)\n"
            "\n"
            "Для навигации центра используйте Navigation/Visible center\n"
            "и режим перспективы Navigation/Perspective\n"
            "Режим перспективы позволяет заглядывать внутрь моделей."
        )
        msgBox.exec()

    def exportStlAction(self):
        self._send_viewer_command({"cmd": "exportstl"})

    def exportBrepAction(self):
        self._send_viewer_command({"cmd": "exportbrep"})

    def to_freecad_action(self):
        self._send_viewer_command({"cmd": "to_freecad"})

    def screenshotAction(self):
        self._send_viewer_command({"cmd": "save_screenshot"})

    def resetAction(self):
        self._send_viewer_command({"cmd": "resetview"})

    def centeringAction(self):
        self._send_viewer_command({"cmd": "centering"})

    def topprojectionAction(self):
        self._send_viewer_command({"cmd": "topprojection"})

    def autoscaleAction(self):
        self._send_viewer_command({"cmd": "autoscale"})

    def trackingAction(self, en):
        self._send_viewer_command({"cmd": "tracking", "en": en})
        self.info_widget.set_tracking_info_status(en)

    def orient1(self):
        self._send_viewer_command({"cmd": "orient1"})

    def orient2(self):
        self._send_viewer_command({"cmd": "orient2"})

    def invalidateCacheAction(self):
        files = zencad.lazy.cache.keys()
        for f in zencad.lazy.cache.keys():
            del zencad.lazy.cache[f]

        if hasattr(zencad.lazy.cache, "clean_tmp"):
            zencad.lazy.cache.clean_tmp()

        print("Invalidate cache: %d files removed" % len(files))

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
                zencad.lazifier.algo().name,
                len(zencad.lazifier.lazy.cache.keys()),
                sizeof_fmt(get_size(zencad.lazifier.cachepath)),
            )
        )
        msgBox.exec()

    def debugInfoAction(self):
        raise NotImplementedError

    def settings(self):
        wdg = zencad.gui.settingswdg.SettingsWidget()
        status = wdg.exec()

        if status == 1:
            self.display_widget.set_msaa_samples(
                Settings.get(["view", "msaa_samples"])
            )
            self.reopen_current()

    def _add_open_action(self, menu, name, path):
        def callback():
            self.open(path)

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

    def create_actions(self):
        self.create_standard_actions()
        self.perspective_checkbox_state = False

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

        self.mTopProjection = self.create_action(
            "TopView", self.topprojectionAction, "TopView"
        )

        self.mOrient1 = self.create_action(
            "Axinometric view", self.orient1, "Orient1")

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
            "Perspective", self.set_perspective, "Set Perspective", checkbox=True, defcheck=False
        )

        self.mVisCenter = self.create_action(
            "Visible center", self.set_center_visible, "Visible center", checkbox=True, defcheck=False
        )

        self.mInvalCache = self.create_action(
            "Invalidate cache", self.invalidateCacheAction, "Invalidate cache"
        )

        self.mCacheInfo = self.create_action(
            "Cache info", self.cacheInfoAction, "Cache info"
        )

        self.mDebugInfo = self.create_action(
            "Debug info", self.debugInfoAction, "Debug info"
        )

        self.mWebManual = self.create_action(
            "Online manual", zencad.gui.util.open_online_manual, "Open online manual in browser", "F1"
        )

    def set_center_visible(self, en):
        self._send_viewer_command({"cmd": "set_center_visible", "en": en})

    def create_menus(self):
        self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.add_new_create_open_standard_actions()
        self.mFileMenu.addSeparator()
        self.exampleMenu = self.mFileMenu.addMenu("Examples")
        self.recentMenu = self.mFileMenu.addMenu("Recent")
        self.mFileMenu.addSeparator()
        self.mFileMenu.addAction(self.mStlExport)
        self.mFileMenu.addAction(self.mBrepExport)
        self.mFileMenu.addAction(self.mToFreeCad)
        self.mFileMenu.addAction(self.mScreen)
        self.mFileMenu.addSeparator()
        self.add_exit_standard_action()

        moduledir = os.path.dirname(__file__)
        self._init_example_menu(
            self.exampleMenu, os.path.join(moduledir, "../examples"))
        self._init_recent_menu(self.recentMenu)

        self.mEditMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.add_editor_standard_action()
        self.mEditMenu.addSeparator()
        self.mEditMenu.addAction(self.mSettings)

        self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
        self.mNavigationMenu.addAction(self.mReset)
        self.mNavigationMenu.addAction(self.mCentering)
        self.mNavigationMenu.addAction(self.mAutoscale)
        self.mNavigationMenu.addAction(self.mTopProjection)
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
        self.mUtilityMenu.addSeparator()
        self.mUtilityMenu.addAction(self.mCacheInfo)
        self.mUtilityMenu.addAction(self.mInvalCache)

        self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
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
        self._send_viewer_command({"cmd": "set_perspective", "en": en})
        self.perspective_checkbox_state = en

    def first_person_mode(self):
        self._send_viewer_command({"cmd": "first_person_mode"})

    def view_only(self, en):
        if en:
            self.menu_bar_height = self.menuBar().height()
            self.menuBar().setFixedHeight(0)
            self.info_widget.setHidden(True)
        else:
            self.menuBar().setFixedHeight(self.menu_bar_height)
            self.info_widget.setHidden(False)

        self.view_mode = en
