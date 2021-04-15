import sys
import os
import time
import signal
import json

import zencad.gui.actions
from zencad.gui.info_widget import InfoWidget
from zencad.settings import Settings

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zenframe.mainwindow import ZenFrame
from zenframe.util import print_to_stderr


class MainWindow(ZenFrame, zencad.gui.actions.MainWindowActionsMixin):
    def __init__(self,
                 title="ZenCad",
                 initial_communicator=None,
                 restore_gui=True
                 ):

        # Init objects
        self.info_widget = InfoWidget()

        super().__init__(
            title=title,
            application_name="zencad",
            initial_communicator=initial_communicator,
            restore_gui=restore_gui)

        # Устанавливается при открытии файла, если при следующем бинде
        # нужно/ненужно произвести восстановить параметры камеры.
        self._last_location = None

    def init_central_widget(self):
        super().init_central_widget()
        self.central_widget_layout().addWidget(self.info_widget)

    def marker_handler(self, qw, data):
        fmt = '.5f'
        x = data["x"]
        y = data["y"]
        z = data["z"]
        idx = qw.upper()
        print("{0}: x:{1}, y:{2}, z:{3}; point3({1},{2},{3})".format(
            idx, format(x, fmt), format(y, fmt), format(z, fmt)))

        self.info_widget.set_marker_data(qw, x, y, z)

    def message_handler(self, data, procpid):
        res = super().message_handler(data, procpid)
        if res:
            return

        try:
            cmd = data["cmd"]
        except:
            return

        if procpid != self._current_client.pid() and data["cmd"] != "finish_screen":
            return

        if cmd == "qmarker":
            self.marker_handler("q", data)
        elif cmd == "wmarker":
            self.marker_handler("w", data)
        elif cmd == "location":
            self._last_location = data["loc"]
        elif cmd == "trackinfo":
            self.info_widget.set_tracking_info(data["data"])
        # elif cmd == "fault":
        #    self.open_fault()
        elif cmd == "evalcache":
            self.evalcache_notification(data)
        else:
            print("Warn: unrecognized command", data)

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
            self.screen_saver.set_subtext(0, "Eval tree: objs:{objs} root:{root}".format(
                root=data["root"][:8], objs=data["len"]))
        if data["subcmd"] == "progress":
            self.screen_saver.set_subtext(
                1, "to load: {}".format(data["toload"]))
            self.screen_saver.set_subtext(
                2, "to eval: {}".format(data["toeval"]))
