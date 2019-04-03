import os
import re
import signal
import inotify

import zencad
import zencad.lazifier
import zencad.viewadapter
import zencad.opengl
from zencad.texteditor import TextEditor

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

ABOUT_TEXT = "CAD system for righteous zen programmers."
BANNER_TEXT = (  # "\n"
    "███████╗███████╗███╗   ██╗ ██████╗ █████╗ ██████╗ \n"
    "╚══███╔╝██╔════╝████╗  ██║██╔════╝██╔══██╗██╔══██╗\n"
    "  ███╔╝ █████╗  ██╔██╗ ██║██║     ███████║██║  ██║\n"
    " ███╔╝  ██╔══╝  ██║╚██╗██║██║     ██╔══██║██║  ██║\n"
    "███████╗███████╗██║ ╚████║╚██████╗██║  ██║██████╔╝\n"
    "╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═════╝ "
)


class ConsoleWidget(QTextEdit):
    def __init__(self):
        class forker(QThread):
            newdata = pyqtSignal(str)

            def __init__(self, console):
                QObject.__init__(self)
                self.console = console
                r, w = os.pipe()
                d = os.dup(1)
                os.close(1)
                os.dup2(w, 1)
                self.d = d
                self.r = r

                global RAWSTDOUT
                RAWSTDOUT = d

            def run(self):
                while 1:
                    readed = os.read(self.r, 512)
                    os.write(self.d, readed)
                    self.newdata.emit(readed.decode("utf-8"))

            def write_native(self, data):
                os.write(self.d, data.encode("utf-8"))

        QTextEdit.__init__(self)
        pallete = self.palette()
        pallete.setColor(QPalette.Base, QColor(30, 30, 30))
        pallete.setColor(QPalette.Text, QColor(255, 255, 255))
        self.setPalette(pallete)

        self.cursor = self.textCursor()
        self.setReadOnly(True)
        self.fork = forker(self)
        self.fork.start()
        self.fork.newdata.connect(self.append)

        font = QFont()
        font.setFamily("Monospace")
        font.setPointSize(10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        metrics = QFontMetrics(font)
        self.setTabStopWidth(metrics.width("    "))

    def print(self, data):
        self.append(data)
        self.fork.write_native(data)

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
                        if "IN_CLOSE_WRITE" in event[1]:
                            print(
                                "widget: {} was rewriten. rerun initial.".format(
                                    self.path
                                )
                            )
                            self.rerun()
                    if self.restart:
                        self.restart = False
                        break
        except Exception as e:
            print("Warning: Rerun thread was finished:", e)

    def rerun(self):
        self.filechanged.emit(self.path)


class MainWindow(QMainWindow):
    class evaluator:
        def __init__(self, ctransler):
            self.ctransler = ctransler

    def __init__(self, scene=None):
        QMainWindow.__init__(self)
        self.lastopened_directory = None
        self.evaluators = []
        self.evaluators_pid = []
        self.setMouseTracking(True)
        self.console = ConsoleWidget()
        self.texteditor = TextEditor()

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)
        self.vsplitter.addWidget(self.console)
        self.hsplitter.addWidget(self.texteditor)
        self.hsplitter.addWidget(self.vsplitter)

        if scene is not None:
            self.wdg = zencad.viewadapter.start_widget(scene)
            self.vsplitter.insertWidget(0, self.wdg)

        # self.inotify_thr = InotifyThread(self)
        # self.inotify_thr.filechanged.connect(self.open_routine)

        self.setCentralWidget(self.hsplitter)
        self.resize(800, 600)
        self.hsplitter.setSizes([400, 500])
        self.move(
            QApplication.desktop().screen().rect().center() - self.rect().center()
        )

        self.createActions()
        self.createMenus()

    def add_view_by_id(self, wid, cmd, pid):
        self.evaluators.append(self.evaluator(cmd))
        container = QWindow.fromWinId(wid)
        cc = QWidget.createWindowContainer(container)
        # cc.setAttribute(Qt.WA_TransparentForMouseEvents);
        self.vsplitter.insertWidget(0, cc)

    def broadcast_send(self, msg, args=()):
        for ev in self.evaluators:
            ev.ctransler.send(msg, args)

    def _add_open_action(self, menu, name, path):
        def callback():
            self.open_routine(path)

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

    def createMenus(self):
        self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.mFileMenu.addAction(self.mOpenAction)
        # 		self.mFileMenu.addAction(self.mTEAction)
        # 		self.mFileMenu.addAction(self.mSaveAction)
        self.exampleMenu = self.mFileMenu.addMenu("Examples")
        # 		self.mFileMenu.addAction(self.mStlExport)
        # 		self.mFileMenu.addAction(self.mBrepExport)
        # 		self.mFileMenu.addAction(self.mToFreeCad)
        self.mFileMenu.addAction(self.mScreen)
        self.mFileMenu.addSeparator()
        self.mFileMenu.addAction(self.mExitAction)

        moduledir = os.path.dirname(__file__)
        self._init_example_menu(self.exampleMenu, os.path.join(moduledir, "examples"))
        #
        self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
        self.mNavigationMenu.addAction(self.mReset)
        self.mNavigationMenu.addAction(self.mCentering)
        self.mNavigationMenu.addAction(self.mAutoscale)
        # 		self.mNavigationMenu.addAction(self.mOrient1)
        # 		self.mNavigationMenu.addAction(self.mOrient2)
        # 		self.mNavigationMenu.addAction(self.mTracking)
        #
        self.mUtilityMenu = self.menuBar().addMenu(self.tr("&Utility"))
        self.mUtilityMenu.addAction(self.mCacheInfo)
        self.mUtilityMenu.addSeparator()
        self.mUtilityMenu.addAction(self.mInvalCache)
        # 		self.mUtilityMenu.addAction(self.mFinishSub)

        self.mViewMenu = self.menuBar().addMenu(self.tr("&View"))
        # 		self.mViewMenu.addAction(self.mFullScreen)
        self.mViewMenu.addAction(self.mHideEditor)
        self.mViewMenu.addAction(self.mHideConsole)

        self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.mHelpMenu.addAction(self.mAboutAction)

    #
    # 		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Devel"))
    # 		self.mHelpMenu.addAction(self.mTestAction)
    # 		self.mHelpMenu.addAction(self.mDebugInfo)

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

    def createActions(self):
        self.mOpenAction = self.create_action("Open", self.openAction, "Open", "Ctrl+O")
        # 		self.mSaveAction = 	self.create_action("Save", 				self.saveAction, 				"Open", 										)#TODO:CTRL+S
        # 		self.mTEAction = 	self.create_action("Open in Editor", 	self.externalTextEditorOpen, 	"Editor", 										"Ctrl+E")
        self.mExitAction = self.create_action("Exit", self.close, "Exit", "Ctrl+Q")
        # 		self.mStlExport = 	self.create_action("Export STL...", 	self.exportStlAction, 			"Export file with external STL-Mesh format")
        # 		self.mToFreeCad= 	self.create_action("To FreeCad", 		self.to_freecad_action, 		"Save temporary BRep representation and save FreeCad script to clipboard to load it")
        # 		self.mBrepExport = 	self.create_action("Export BREP...", 	self.exportBrepAction, 			"Export file in BREP format")
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
        # 		self.mOrient1 = 	self.create_action("Axinometric view", 	self.orient1, 					"Orient1")
        # 		self.mOrient2 = 	self.create_action("Free rotation view",self.orient2, 					"Orient2")
        # 		self.mTracking = 	self.create_action("Tracking", 			self.trackingAction, 			"Tracking",				checkbox=True)
        # 		self.mTestAction = 	self.create_action("TestAction", 		self.testAction, 				"TestAction")
        self.mInvalCache = self.create_action(
            "Invalidate cache", self.invalidateCacheAction, "Invalidate cache"
        )
        self.mCacheInfo = self.create_action(
            "Cache info", self.cacheInfoAction, "Cache info"
        )
        # 		self.mFinishSub = 	self.create_action("Finish subprocess", self.finishSubProcess, 			"Finish subprocess")
        # 		self.mDebugInfo = 	self.create_action("Debug info", 		self.debugInfoAction, 			"Debug info")
        self.mHideConsole = self.create_action(
            "Hide console", self.hideConsole, "Hide console", checkbox=True
        )
        self.mHideEditor = self.create_action(
            "Hide editor", self.hideEditor, "Hide editor", checkbox=True
        )

    # 		self.mFullScreen = 	self.create_action("Full screen", 		self.fullScreen, 				"Full screen",									"F11")

    def invalidateCacheAction(self):
        files = zencad.lazy.cache.keys()
        for f in zencad.lazy.cache.keys():
            del zencad.lazy.cache[f]
        print("invalidate cache: %d files removed" % len(files))

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

    def hideConsole(self, en):
        self.console.setHidden(en)

    def hideEditor(self, en):
        self.texteditor.setHidden(en)

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

    def screenshotAction(self):
        filters = "*.png;;*.bmp;;*.jpg;;*.*"
        defaultFilter = "*.png"

        path = QFileDialog.getSaveFileName(
            self, "Dump image", QDir.currentPath(), filters, defaultFilter
        )

        path = path[0]

        self.evaluators[0].ctransler.send("screen", [path])

    def centeringAction(self):
        self.evaluators[0].ctransler.send("centering", [])

    def autoscaleAction(self):
        self.evaluators[0].ctransler.send("autoscale", [])

    def resetAction(self):
        self.evaluators[0].ctransler.send("resetview", [])

    def open_routine(self, path):
        import zencad.unbound

        # global started_by, edited
        filetext = open(path).read()
        repattern1 = re.compile(r"import *zencad|from *zencad *import")

        zencad_search = repattern1.search(filetext)
        print("widget: try open {}".format(path))

        if zencad_search is not None:
            if len(self.evaluators) > 1:
                self.evaluators[1].ctransler.send("stopworld", args=())
                self.evaluators[1].ctransler.stop()
                del self.evaluators[1]

            ctransler = zencad.unbound.start_viewadapter_unbound(self, path)
            neval = self.evaluator(ctransler)
            self.evaluators.append(neval)
            neval.ctransler.log_signal.connect(self.console.print)

            self.texteditor.open(path)
            self.inotify_thr.init_notifier(path)

            def readytoshow(wid):
                self.vsplitter
                container = QWindow.fromWinId(wid)
                cc = QWidget.createWindowContainer(container)
                oldw = self.vsplitter.replaceWidget(0, cc)
                self.evaluators[1].ctransler.send("sync", args=())
                self.evaluators[0].ctransler.send("stopworld", args=())
                del self.evaluators[0]
                QTimer.singleShot(200, lambda: oldw.deleteLater())
                print("widget: scene was updated")

            ctransler.readytoshow_signal.connect(readytoshow)
        # 	self.rerun_label_on_slot()
        # 	if self.lastopened != path:
        # 		self.rescale_on_finish = True
        # 	self.lastopened = path
        # 	started_by = path
        # 	os.chdir(os.path.dirname(path))
        # 	self.external_rerun_signal.emit()

        # ctransler = self.evaluators[0].ctransler
        # ctransler.send("stopworld", [])

        # self.texteditor.setPlainText(filetext)

    def openAction(self):
        filters = "*.py;;*.*"
        defaultFilter = "*.py"

        startpath = (
            QDir.currentPath()
            if self.lastopened_directory is None
            else self.lastopened_directory
        )

        path = QFileDialog.getOpenFileName(
            self, "Open File", startpath, filters, defaultFilter
        )

        if path[0] == "":
            return

        self.lastopened_directory = os.path.dirname(path[0])
        self.open_routine(path[0])

    def bound(self, bound):
        apino = bound[0]
        wid = int(bound[1])
        pid = int(bound[2])
        path = bound[3]
        self.evaluators.append(self.evaluator(zencad.rpc.ServerTransler(self, apino)))
        self.evaluators_pid.append(pid)
        container = QWindow.fromWinId(wid)
        cc = QWidget.createWindowContainer(container)
        self.vsplitter.insertWidget(0, cc)

        self.texteditor.open(path)
        self.inotify_thr.init_notifier(path)


# def start_application(bound=None):
# 	app = QApplication([])
# 	pal = app.palette();
# 	pal.setColor(QPalette.Window, QColor(160,161,165));
# 	app.setPalette(pal);
#
# 	mw = MainWindow()
# 	if bound is not None:
# 		mw.bound(bound)
# 	mw.show()
#
# 	def stopworld():
# 		mw.broadcast_send("stopworld")
# 		app.quit()
#
# 	app.lastWindowClosed.connect(stopworld)
# 	app.exec()


def start(scene, *args, **kwargs):
    app = QApplication([])
    zencad.opengl.init_opengl()

    pal = app.palette()
    pal.setColor(QPalette.Window, QColor(160, 161, 165))
    app.setPalette(pal)

    mw = MainWindow(scene)

    def stopworld():
        mw.stop()
        app.quit()

    app.lastWindowClosed.connect(stopworld)

    mw.show()
    app.exec()
