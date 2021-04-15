from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import tempfile
import subprocess
import signal

import zencad.gui.util
import zencad.gui.settingswdg

from zencad.settings import Settings
from zenframe.actions import ZenFrameActionsMixin

ABOUT_TEXT = "CAD system for righteous zen programmers."
BANNER_TEXT = (  # "\n"
    "███████╗███████╗███╗   ██╗ ██████╗ █████╗ ██████╗ \n"
    "╚══███╔╝██╔════╝████╗  ██║██╔════╝██╔══██╗██╔══██╗\n"
    "  ███╔╝ █████╗  ██╔██╗ ██║██║     ███████║██║  ██║\n"
    " ███╔╝  ██╔══╝  ██║╚██╗██║██║     ██╔══██║██║  ██║\n"
    "███████╗███████╗██║ ╚████║╚██████╗██║  ██║██████╔╝\n"
    "╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═════╝ "
)


class MainWindowActionsMixin(ZenFrameActionsMixin):
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

    def exportStlAction(self):
        self._current_client.send({"cmd": "exportstl"})

    def exportBrepAction(self):
        self._current_client.send({"cmd": "exportbrep"})

    def to_freecad_action(self):
        self._current_client.send({"cmd": "to_freecad"})

    def screenshotAction(self):
        self._current_client.send({"cmd": "save_screenshot"})

    def resetAction(self):
        self._current_client.send({"cmd": "resetview"})

    def centeringAction(self):
        self._current_client.send({"cmd": "centering"})

    def autoscaleAction(self):
        self._current_client.send({"cmd": "autoscale"})

    def trackingAction(self, en):
        self._current_client.send({"cmd": "tracking", "en": en})
        self.info_widget.set_tracking_info_status(en)

    def orient1(self):
        self._current_client.send({"cmd": "orient1"})

    def orient2(self):
        self._current_client.send({"cmd": "orient2"})

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

    def coordsDifferenceMode(self, en):
        self.info_widget.coords_difference_mode = en
        self.info_widget.update_dist()

    def settings(self):
        wdg = zencad.gui.settingswdg.SettingsWidget()
        status = wdg.exec()

        if status == 1 and self.use_sleeped_process:
            self.remake_sleeped_client()
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
        super().create_actions()
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
        self._current_client.send(
            {"cmd": "set_center_visible", "en": en})

    def create_menus(self):
        self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.add_new_create_open_standart_actions()
        self.mFileMenu.addSeparator()
        self.exampleMenu = self.mFileMenu.addMenu("Examples")
        self.recentMenu = self.mFileMenu.addMenu("Recent")
        self.mFileMenu.addSeparator()
        self.mFileMenu.addAction(self.mStlExport)
        self.mFileMenu.addAction(self.mBrepExport)
        self.mFileMenu.addAction(self.mToFreeCad)
        self.mFileMenu.addAction(self.mScreen)
        self.mFileMenu.addSeparator()
        self.add_exit_standart_action()

        moduledir = os.path.dirname(__file__)
        self._init_example_menu(
            self.exampleMenu, os.path.join(moduledir, "../examples"))
        self._init_recent_menu(self.recentMenu)

        self.mEditMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.add_editor_standart_action()
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
        if self._current_client:
            self._current_client.send(
                {"cmd": "set_perspective", "en": en})
        self.perspective_checkbox_state = en

    def first_person_mode(self):
        self._current_client.send({"cmd": "first_person_mode"})

    def view_only(self, en):
        if en:
            self.menu_bar_height = self.menuBar().height()
            self.menuBar().setFixedHeight(0)
            self.info_widget.setHidden(True)
        else:
            self.menuBar().setFixedHeight(self.menu_bar_height)
            self.info_widget.setHidden(False)

        self.view_mode = en
