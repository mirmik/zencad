import sys
import os
import time
import signal
import json
from zencad.frame.util import print_to_stderr

import zencad.gui.actions
from zencad.gui.info_widget import InfoWidget
from zencad.gui.display_unbounded import start_unbounded_worker, spawn_sleeped_worker
from zencad.gui.startwdg import StartDialog

from zencad.settings import Settings

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zencad.configuration import Configuration
from zencad.frame.mainwindow import ZenFrame

if Configuration.FILTER_QT_WARNINGS:
    QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')




class MainWindow(ZenFrame, zencad.gui.actions.MainWindowActionsMixin):
    def __init__(self,
                 title="ZenCad",
                 initial_communicator=None,
                 restore_gui=True,
                 sleeped_optimization=True
                 ):

        # Init objects
        self.info_widget = InfoWidget()

        super().__init__(
            title=title,
            sleeped_optimization=sleeped_optimization,
            initial_communicator=initial_communicator,
            restore_gui=restore_gui)

        # Init variables
        self._openlock = QtCore.QMutex(QtCore.QMutex.Recursive)
        self._inited0 = False  # Show event was invoked first time

        # Путь с именем текщего открытого/открываемого файла.
        self._current_opened = None

        # Устанавливается при открытии файла, если при следующем бинде
        # нужно/ненужно произвести восстановить параметры камеры.
        self._last_location = None

        # Modes
        self._bind_mode = True  # Bind widget to embed window

    def spawn(self, sleeped=False, openpath="", need_prescale=False, size=(640,480)):
        return start_unbounded_worker(path=openpath,
                               need_prescale=need_prescale,
                               size=size,
                               sleeped=sleeped)

    def init_central_widget(self):
        super().init_central_widget()
        self.central_widget_layout().addWidget(self.info_widget)

    def showEvent(self, event):
        if not self._inited0:
            self._inited0 = True

    def open_declared(self, path):
        self._current_opened = path
        self.texteditor.open(path)

    def new_worker_message(self, data, procpid):
        try:
            cmd = data["cmd"]
        except:
            return

        if procpid != self._current_client.pid() and data["cmd"] != "finish_screen":
            return

        # TODO: Переделать в словарь
        if cmd == 'bindwin':
            self.bind_window(winid=data['id'], pid=data["pid"])
        # elif cmd == 'setopened':
        #    self.set_current_opened(path=data['path'])
        # elif cmd == 'clientpid':
        #    self.clientpid = data['pid']
        elif cmd == "except":
            print(f"Exception in subprocess with executable path: {data['path']}")
            print(data["header"])
            print(data["tb"])
        elif cmd == "qmarker":
            self.marker_handler("q", data)
        elif cmd == "wmarker":
            self.marker_handler("w", data)
        elif cmd == "location":
            self._last_location = data["loc"]
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
        elif cmd == "evalcache":
            self.evalcache_notification(data)
        else:
            print("Warn: unrecognized command", data)

    #def closeEvent(self, ev):
    #    super().closeEvent(ev)

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

    def synchronize_subprocess_state(self):
        """
            Пересылаем на ту сторону информацию об опциях интерфейса.
        """

        if self.is_reopen_mode() and self._last_location is not None:
            self._current_client.send(
                {"cmd": "location", "loc": self._last_location})
            
        self._current_client.send(
            {"cmd": "set_perspective", "en": self.perspective_checkbox_state})
        self._current_client.send({"cmd": "redraw"})
        super().synchronize_subprocess_state()


    def evalcache_notification(self, data):
        if data["subcmd"] == "newtree":
            self.screen_saver.set_subtext(0, "Eval tree: objs:{objs} root:{root}".format(root=data["root"][:8], objs=data["len"]))
        if data["subcmd"] == "progress":
            self.screen_saver.set_subtext(1, "to load: {}".format(data["toload"]))
            self.screen_saver.set_subtext(2, "to eval: {}".format(data["toeval"]))


def start_application(openpath=None, none=False, unbound=False, norestore=False, sleeped_optimization=True):
    QAPP = QtWidgets.QApplication(sys.argv[1:])
    initial_communicator = None

    if unbound:
        # Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
        # через ретранслятор. Теперь все консольные сообщения будуут обвешиваться
        # тегами и поступать на коммуникатор.
        retransler = ConsoleRetransler(sys.stdout)
        retransler.start()

        # Коммуникатор будет слать сообщения на скрытый файл,
        # тоесть, на истинный stdout
        initial_communicator = Communicator(
            ifile=sys.stdin, ofile=retransler.new_file)

        # Показываем ретранслятору его коммуникатор.
        retransler.set_communicator(initial_communicator)

        data = initial_communicator.simple_read()
        dct0 = json.loads(data)

        initial_communicator.declared_opposite_pid = int(dct0["data"])

    if openpath is None and not none and not unbound:
        if Settings.get(["gui", "start_widget"]) == "true":
            strt_dialog = zencad.gui.startwdg.StartDialog()
            strt_dialog.exec()

            if strt_dialog.result() == 0:
                return

            openpath = strt_dialog.openpath

        else:
            openpath = zencad.gui.util.create_temporary_file(
                zencad_template=True)

    MAINWINDOW = MainWindow(
        initial_communicator=initial_communicator,
        restore_gui=not norestore,
        sleeped_optimization=sleeped_optimization)

    if unbound:
        initial_communicator.bind_handler(MAINWINDOW.new_worker_message)
        initial_communicator.start_listen()

    if openpath:
        if not unbound:
            MAINWINDOW.open(openpath)
        else:
            MAINWINDOW.open_declared(openpath)

    timer = QtCore.QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.
    
    MAINWINDOW.show()
    QAPP.exec()
