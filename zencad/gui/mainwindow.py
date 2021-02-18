import sys
import os
import time
import signal
import json
from zencad.util import print_to_stderr

import zencad.gui.actions
from zencad.gui.inotifier import InotifyThread
from zencad.gui.info_widget import InfoWidget
from zencad.gui.screen_saver import ScreenSaverWidget
from zencad.gui.console import ConsoleWidget
from zencad.gui.text_editor import TextEditor
from zencad.gui.display_unbounded import start_unbounded_worker, spawn_sleeped_worker
from zencad.gui.startwdg import StartDialog


from zencad.gui.retransler import ConsoleRetransler
from zencad.gui.communicator import Communicator

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

import zencad.configuration
if zencad.configuration.FILTER_QT_WARNINGS:
    QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')


class MainWindow(QtWidgets.QMainWindow, zencad.gui.actions.MainWindowActionsMixin):
    def __init__(self,
                 title="ZenCad",
                 sleeped_optimization=zencad.configuration.SLEEPED_OPTIMIZATION,
                 initial_process_communicator=None
                 ):

        super().__init__()

        # Init objects
        self.console = ConsoleWidget()
        self.texteditor = TextEditor()
        self.info_widget = InfoWidget()
        self.notifier = InotifyThread(self)
        self.screen_saver = ScreenSaverWidget()
        self.initial_process_communicator = initial_process_communicator

        # Init variables
        self._keep_alive_pids = []
        self._inited0 = False
        self._bind_mode = True
        self._sleeped_optimization = sleeped_optimization
        self._current_opened = None
        self._openlock = QtCore.QMutex(QtCore.QMutex.Recursive)
        self._current_client_communicator = None
        self._sleeped_communicator = None

        # Modes
        self._fscreen_mode = False

        # Reference Holder
        self._embededs_holder = {}
        self._client_communicators = {}

        # Init Gui
        self.setWindowTitle(title)
        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.init_central_widget()

        # Bind signals
        self.notifier.changed.connect(self.reopen_current)

        if self._sleeped_optimization:
            self.make_sleeped_thread()

        if initial_process_communicator:
            print_to_stderr("initial_process_communicator", initial_process_communicator.subproc_pid())
            self._current_client_communicator = initial_process_communicator
            self._client_communicators[initial_process_communicator.subproc_pid()] = initial_process_communicator
            self._keep_alive_pids.append(initial_process_communicator.subproc_pid())

    def make_sleeped_thread(self, kill_prev=True):
        if self._sleeped_communicator and kill_prev:
            self._sleeped_communicator.subproc.terminate()

        self._sleeped_communicator = spawn_sleeped_worker()

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

        self.cw_layout.setContentsMargins(0, 0, 0, 0)
        self.cw_layout.setSpacing(0)

        self.setCentralWidget(self.cw)
        self.update()

        self.resize(640, 480)

    def showEvent(self, event):
        if not self._inited0:
            self.hsplitter.refresh()
            self.vsplitter.refresh()
            self.vsplitter.setSizes([self.height()*5/8, self.height()*3/8])
            self.hsplitter.setSizes([self.width()*3/8, self.width()*5/8])
            self.hsplitter.refresh()
            self.vsplitter.refresh()
            self._inited0 = True

    def reopen_current(self):
        self._openlock.lock()
        self.open(openpath=self._current_opened, update_texteditor=False)
        self.texteditor.reopen()
        self._openlock.unlock()

    def current_opened(self):
        return self._current_opened

    def open(self, openpath, update_texteditor=True):
        self._openlock.lock()

        self._current_opened = openpath
        if update_texteditor:
            self.texteditor.open(openpath)

        self.notifier.clear()
        self.notifier.add_target(openpath)

        need_prescale = False

        if self._sleeped_optimization:
            client_communicator = self._sleeped_communicator
            size = self.vsplitter.widget(0).size()
            size = "{},{}".format(size.width(), size.height())
            client_communicator.send({
                "cmd": "unsleep",
                "path": openpath,
                "need_prescale": need_prescale,
                "size": size
            })

            self.make_sleeped_thread(False)

        else:
            client_communicator = start_unbounded_worker(path=openpath,
                                                         need_prescale=need_prescale,
                                                         size=self.vsplitter.widget(0).size())

        self._current_client_communicator = client_communicator
        self._client_communicators[
            client_communicator.subproc.pid] = client_communicator

        self._current_client_communicator.oposite_clossed.connect(
            self.delete_communicator)
        self._current_client_communicator.bind_handler(self.new_worker_message)
        self._current_client_communicator.start_listen()

        self._openlock.unlock()

    def open_declared(self, path):
        self._current_opened = path
        self.texteditor.open(path)

    def finalize_subprocess(self, communicator):
        pid = communicator.subproc_pid()
        os.kill(communicator.subproc.pid, signal.SIGTERM)

    def subprocess_finalization_do(self):
        to_delete = []
        current_pid = self._current_client_communicator.subproc_pid()
        for pid in self._client_communicators:
            if (
                    not pid == current_pid and
                    not pid in self._keep_alive_pids):
                self.finalize_subprocess(
                    communicator=self._client_communicators[pid])
                to_delete.append(pid)

        for pid in to_delete:
            del self._client_communicators[pid]
            del self._embededs_holder[pid]

        assert(len(self._client_communicators) == len(self._embededs_holder))

    def new_worker_message(self, data, procpid):
        try:
            cmd = data["cmd"]
        except:
            print("Warn: new_worker_message: message without 'cmd' field")
            returna

        if procpid != self._current_client_communicator.subproc_pid() and data["cmd"] != "finish_screen":
            return

        # TODO: Переделать в словарь
        if cmd == 'bindwin':
            self.bind_window(winid=data['id'], pid=data["pid"])
        # elif cmd == 'setopened':
        #    self.set_current_opened(path=data['path'])
        # elif cmd == 'clientpid':
        #    self.clientpid = data['pid']
        elif cmd == "qmarker":
            self.marker_handler("q", data)
        elif cmd == "wmarker":
            self.marker_handler("w", data)
        # elif cmd == "location":
        #    self.location_update_handle(data["loc"])
        # elif cmd == "keypressed":
        #    self.internal_key_pressed(data["key"])
        elif cmd == "keypressed_raw":
            self.internal_key_pressed_raw(
                data["key"], data["modifiers"], data["text"])
        # elif cmd == "keyreleased_raw":
        #    self.internal_key_released_raw(data["key"], data["modifiers"])
        elif cmd == "console":
            self.internal_console_request(data["data"])
        # elif cmd == "trackinfo":
        #    self.info_widget.set_tracking_info(data["data"])
        # elif cmd == "finish_screen":
        #    self.finish_screen(data["data"][0], data["data"][1], procpid)
        # elif cmd == "fault":
        #    self.open_fault()
        # elif cmd == "evalcache":
        #    self.evalcache_notification(data)
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

            # Удерживаем ссылки на объекты, чтобы избежать
            # произвола от сборщика мусора
            self._embededs_holder[pid] = (
                (self.embeded_window, self.embeded_window_container))
            self.setWindowTitle(self._current_opened)

            #self.open_in_progress = False

            #self._current_client_communicator.send({"cmd": "show"})

            # self.synchronize_subprocess_state()

            # time.sleep(0.1)
            # self.update()
        except Exception as ex:
            self._openlock.unlock()
            print_to_stderr("exception on window bind", ex)
            raise ex

        self.subprocess_finalization_do()
        self._openlock.unlock()

    def delete_communicator(self):
        """Вызывается по сигналу об окончании сеанса"""
        self._openlock.lock()

        comm = self.sender()
        comm.stop_listen()
        #
        # if comm in self.client_finalization_list:
        #	self.client_finalization_list.remove(comm)
        #
        #del self.communicator_dictionary[comm.subproc.pid]
        #
        # clean client_finalization_list from uncostistent nodes
        # for comm in self.client_finalization_list:
        #	if comm not in self.communicator_dictionary.values():
        #		self.client_finalization_list.remove(comm)

        self._openlock.unlock()

    def closeEvent(self, event):
        self.notifier.finish()
        self.notifier.wait()

    def internal_console_request(self, data):
        self.console.write(data)

    def internal_key_pressed_raw(self, key, modifiers, text):
        self.texteditor.setFocus()
        modifiers = QtCore.Qt.KeyboardModifiers()
        event = QtGui.QKeyEvent(
            QtCore.QEvent.KeyPress, key, QtCore.Qt.KeyboardModifier(modifiers), text)
        QtGui.QGuiApplication.postEvent(self.texteditor, event)

    def internal_key_released_raw(self, key, modifiers):
        modifiers = QtCore.Qt.KeyboardModifiers()
        event = QtGui.QKeyEvent(QtCore.QEvent.KeyRelease,
                                key, QtCore.Qt.KeyboardModifier(modifiers))
        QtGui.QGuiApplication.postEvent(self.texteditor, event)


def start_application(openpath=None, none=False, unbound=False):
    QAPP = QtWidgets.QApplication(sys.argv[1:])
    initial_process_communicator = None

    if unbound:
        # Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
        # через ретранслятор. Теперь все консольные сообщения будуут обвешиваться
        # тегами и поступать на коммуникатор.
        retransler = ConsoleRetransler(sys.stdout)
        retransler.start()
    
        # Коммуникатор будет слать сообщения на скрытый файл,
        # тоесть, на истинный stdout
        initial_process_communicator = Communicator(
            ifile=sys.stdin, ofile=retransler.new_file)

        # Показываем ретранслятору его коммуникатор.
        retransler.set_communicator(initial_process_communicator)

        data = initial_process_communicator.simple_read()
        dct0 = json.loads(data)

        initial_process_communicator.declared_opposite_pid = int(dct0["data"])

    if openpath is None and not none and not unbound:
        if zencad.settings.list()["gui"]["start_widget"] == "true":
            strt_dialog = zencad.gui.startwdg.StartDialog()
            strt_dialog.exec()

            if strt_dialog.result() == 0:
                return

            openpath = strt_dialog.openpath

        else:
            openpath = zencad.gui.util.create_temporary_file(
                zencad_template=True)

    MAINWINDOW = MainWindow(
        initial_process_communicator=initial_process_communicator)

    if unbound:
        initial_process_communicator.bind_handler(MAINWINDOW.new_worker_message)
        initial_process_communicator.start_listen()

    if openpath:
        if not unbound:
            MAINWINDOW.open(openpath)
        else:
            MAINWINDOW.open_declared(openpath)

    MAINWINDOW.show()
    QAPP.exec()
