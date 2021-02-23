from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import tempfile
import subprocess
import os

from zencad.settings import Settings
import zencad.frame.util

class ZenFrameActionsMixin:
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

    def create_actions(self):
        self.mCreateAction = self.create_action(
            "CreateNew...", self.createNewAction, "Create"
        )
        
        self.mCreateTemp = self.create_action(
            "NewTemporary", self.createNewTemporary, "CreateTemporary", "Ctrl+N"
        )
        
        self.mOpenAction = self.create_action(
            "Open...", self.openAction, "Open", "Ctrl+O"
        )
        
        self.mSaveAction = self.create_action(
            "Save", self.saveAction, "Save", "Ctrl+S")
        
        self.mSaveAs = self.create_action(
            "SaveAs...", self.saveAsAction, "SaveAs...")
        
        self.mTEAction = self.create_action(
            "Open in Editor", self.externalTextEditorOpen, "Editor", "Ctrl+E"
        )

        self.mExitAction = self.create_action(
            "Exit", self.close, "Exit", "Ctrl+Q")
        
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

        self.mViewOnly = self.create_action(
            "Hide Bars", self.viewOnly, "Hide bars", "F9"
        )

        self.mReopenCurrent = self.create_action(
            "Reopen current", self.reopen_current, "Reopen current", "Ctrl+R"
        )

        self.mFrameAboutAction = self.create_action(
            "About", self.frameAboutAction, "About the ZenFrame library"
        )

    def create_menus(self):
        self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.add_new_create_open_standart_actions()
        self.mFileMenu.addSeparator()
        self.add_exit_standart_action()

        self.mEditMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.add_editor_standart_action()

        self.mUtilityMenu = self.menuBar().addMenu(self.tr("&Utility"))
        self.mUtilityMenu.addAction(self.mAutoUpdate)

        self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
        self.mViewMenu.addAction(self.mFullScreen)
        self.mViewMenu.addAction(self.mDisplayMode)
        self.mViewMenu.addAction(self.mViewOnly)
        self.mViewMenu.addAction(self.mHideEditor)
        self.mViewMenu.addAction(self.mHideConsole)

        self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.mHelpMenu.addAction(self.mFrameAboutAction)

    def add_new_create_open_standart_actions(self):
        self.mFileMenu.addAction(self.mReopenCurrent)
        self.mFileMenu.addAction(self.mOpenAction)
        self.mFileMenu.addAction(self.mCreateTemp)
        self.mFileMenu.addAction(self.mCreateAction)
        self.mFileMenu.addAction(self.mSaveAction)
        self.mFileMenu.addAction(self.mSaveAs)
        
    def add_exit_standart_action(self):
        self.mFileMenu.addAction(self.mExitAction)

    def add_editor_standart_action(self):
        self.mEditMenu.addAction(self.mTEAction)

    def frameAboutAction(self):
        QMessageBox.about(
            self,
            self.tr("About ZenFrame"),
            (
                "<p>HelloWorld"
            ),
        )


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
        curopen = self.current_opened()
        path = zencad.frame.util.open_file_dialog(
            self,
            directory=None if curopen is None else os.path.dirname(curopen))

        if path[0] == "":
            return

        self.open(path[0])

    def saveAction(self):
        self.texteditor.save()

    def saveAsAction(self):
        path, template = zencad.frame.util.save_file_dialog(self)

        if path == "":
            return

        self.texteditor.save_as(path)

    def externalTextEditorOpen(self):
        cmd = Settings.get(["gui", "text_editor"])
        subprocess.Popen(cmd.format(path=self.current_opened()), shell=True)

    def hideConsole(self, en):
        self.console.setHidden(en)

    def hideEditor(self, en):
        self.texteditor.setEnabled(not en)
        self.texteditor.setHidden(en)

        if self._current_client is not None:
            self._current_client.send(
                {"cmd": "keyboard_retranslate", "en": not en})


    def fullScreen(self):
        if not self._fscreen_mode:
            self.showFullScreen()
            self._fscreen_mode = True
        else:
            self.showNormal()
            self._fscreen_mode = False

    def view_only(self, en):
        if en:
            self.menu_bar_height = self.menuBar().height()
            self.menuBar().setFixedHeight(0)
        else:
            self.menuBar().setFixedHeight(self.menu_bar_height)

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
        self.display_mode_enable(
            not (self.texteditor.isHidden() or self.console.isHidden()))


    def auto_update(self, en):
        if en:
            self.notifier.control_unlock()
        else:
            self.notifier.control_lock()
