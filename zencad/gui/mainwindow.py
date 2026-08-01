import sys
import os
import time
import signal
import json
import threading

import zencad.gui.actions
from zencad.gui.info_widget import InfoWidget
from zencad.settings import Settings

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zenframe.mainwindow import ZenFrame
from zenframe.util import print_to_stderr


class MainWindow(ZenFrame, zencad.gui.actions.MainWindowActionsMixin):
    runner_message = QtCore.pyqtSignal(object)
    scene_patch_ready = QtCore.pyqtSignal()

    def __init__(self,
                 title="ZenCad",
                 initial_communicator=None,
                 restore_gui=True,
                 managed_runtime=True,
                 ):

        # Init objects
        self.info_widget = InfoWidget()
        self._managed_runtime_requested = managed_runtime
        self._runner_supervisor = None
        self._pending_snapshots = {}
        self._generation_statuses = {}
        self._scene_patch_coalescer = None
        self._scene_patch_lock = threading.Lock()
        self._scene_patch_notification_pending = False
        self._scene_patch_bridge_error = None
        self._failed_live_generation = None

        super().__init__(
            title=title,
            application_name="zencad",
            initial_communicator=initial_communicator,
            restore_gui=restore_gui)

        if managed_runtime:
            from zencad.runtime import RunnerSupervisor, ScenePatchCoalescer

            self.use_sleeped_process = False
            self.runner_message.connect(
                self._handle_runner_message,
                QtCore.Qt.QueuedConnection,
            )
            self.scene_patch_ready.connect(
                self._apply_pending_scene_patch,
                QtCore.Qt.QueuedConnection,
            )
            self._runner_supervisor = RunnerSupervisor(
                on_message=self._queue_runner_message,
                record_scene_patches=False,
            )
            self._scene_patch_coalescer = ScenePatchCoalescer()
            self.display_widget.set_input_event_sink(
                self._forward_input_event
            )

        # Устанавливается при открытии файла, если при следующем бинде
        # нужно/ненужно произвести восстановить параметры камеры.
        self._last_location = None

    def spawn_process(self, application_name):
        if self._managed_runtime_requested:
            return None
        return super().spawn_process(application_name)

    def init_central_widget(self):
        super().init_central_widget()
        if self._managed_runtime_requested:
            from zencad.gui.display import DisplayWidget

            # Give Qt the final native parent before OCCT binds to winId().
            # Reparenting an already-created native widget can replace its XID
            # and leave Xw_Window drawing into the old invisible window.
            self.screen_saver.setParent(None)
            self.display_widget = DisplayWidget(parent=self.vsplitter)
            self.vsplitter.insertWidget(0, self.display_widget)
            self.screen_saver.hide()
        self.central_widget_layout().addWidget(self.info_widget)

    def open(self, openpath, update_texteditor=True):
        if not self._managed_runtime_requested:
            return super().open(openpath, update_texteditor)

        self._openlock.lock()
        try:
            self._reopen_mode = openpath == self._current_opened
            self._current_opened = openpath
            if update_texteditor:
                self.texteditor.open(openpath)

            self.notifier.clear()
            self.notifier.add_target(openpath)
            self.console.clear()
            self.setWindowTitle(openpath)
            self.openStartEvent(openpath)
            generation = self._runner_supervisor.start(openpath)
            self._pending_snapshots.clear()
            self._generation_statuses.clear()
            with self._scene_patch_lock:
                self._scene_patch_coalescer.clear()
                self._scene_patch_notification_pending = False
                self._scene_patch_bridge_error = None
            self._failed_live_generation = None
            return generation
        finally:
            self._openlock.unlock()

    def enable_display_changed_mode(self):
        if not self._managed_runtime_requested:
            return super().enable_display_changed_mode()
        self.statusBar().showMessage("Calculating scene…")

    def _queue_runner_message(self, message):
        """Coalesce patches before they can fill the queued Qt event stream."""
        if message.message_type != "scene_patch":
            self.runner_message.emit(message)
            return
        should_notify = False
        with self._scene_patch_lock:
            try:
                self._scene_patch_coalescer.push(message.scene_patch)
            except Exception as exception:
                self._scene_patch_bridge_error = exception
                self._scene_patch_coalescer.clear()
            if not self._scene_patch_notification_pending:
                self._scene_patch_notification_pending = True
                should_notify = True
        if should_notify:
            self.scene_patch_ready.emit()

    def _forward_input_event(self, message_type, data):
        if self._runner_supervisor is None:
            return False
        try:
            return self._runner_supervisor.send_input(message_type, data)
        except Exception:
            import traceback

            self.console.write(traceback.format_exc())
            self._fail_live_scene("Input transport failed")
            return False

    def _progress_text(self, payload):
        if payload.get("phase"):
            return "Calculating scene: {}".format(payload["phase"])
        if payload.get("subcmd") == "progress":
            return "Calculating scene: load {}, evaluate {}".format(
                payload.get("toload", "?"), payload.get("toeval", "?")
            )
        if payload.get("subcmd") == "newtree":
            return "Calculating scene: {} objects".format(
                payload.get("len", "?")
            )
        return "Calculating scene…"

    @QtCore.pyqtSlot(object)
    def _handle_runner_message(self, message):
        message_type = message.message_type
        generation = message.generation
        if generation != self._runner_supervisor.current_generation:
            # A callback can already be queued in Qt when a new generation is
            # started.  Recheck freshness on the GUI side before staging or
            # committing anything.
            return
        if (
            generation == self._failed_live_generation
            and message_type in {"scene", "ready", "scene_patch"}
        ):
            return

        if message_type == "run":
            self.enable_display_changed_mode()
        elif message_type == "progress":
            self.statusBar().showMessage(self._progress_text(message.payload))
        elif message_type == "output":
            self.console.write(message.payload.get("text", ""))
        elif message_type == "scene":
            self._pending_snapshots[generation] = message.snapshot
        elif message_type == "ready":
            snapshot = self._pending_snapshots.get(generation)
            if snapshot is None:
                self._fail_live_scene(
                    "Runner became ready without an initial scene"
                )
                return
            if not message.payload.get("animated"):
                self.statusBar().showMessage("Finalizing scene…")
                return
            self._pending_snapshots.pop(generation, None)
            try:
                self.display_widget.scene_presenter.apply(
                    snapshot,
                    scene_revision=message.payload.get("scene_revision", 0),
                )
            except Exception:
                import traceback

                self.console.write(traceback.format_exc())
                self._fail_live_scene("Scene presentation failed")
                return
            self.statusBar().showMessage("Animation running")
        elif message_type == "error":
            self._apply_pending_scene_patch()
            details = message.payload.get("traceback")
            if not details:
                details = "{}: {}\n".format(
                    message.payload.get("exception_type", "RunnerError"),
                    message.payload.get("message", ""),
                )
            self.console.write(details)
            if (
                self.display_widget.scene_presenter.committed_generation
                == generation
            ):
                self.statusBar().showMessage("Animation failed; last frame retained")
            else:
                self.statusBar().showMessage("Scene calculation failed")
        elif message_type == "finished":
            status = message.payload.get("status")
            snapshot = self._pending_snapshots.pop(generation, None)
            if status == "success" and snapshot is not None:
                try:
                    self.display_widget.apply_snapshot(snapshot)
                except Exception:
                    import traceback

                    self.console.write(traceback.format_exc())
                    self.statusBar().showMessage("Scene presentation failed")
                else:
                    self.statusBar().showMessage("Scene ready", 2000)
            elif (
                status == "success"
                and self.display_widget.scene_presenter.committed_generation
                == generation
            ):
                self.statusBar().showMessage("Scene ready", 2000)
            elif status == "success":
                self.statusBar().showMessage("Script produced no scene", 3000)
            elif (
                status == "cancelled"
                and generation != self._failed_live_generation
            ):
                self.statusBar().showMessage("Scene calculation cancelled", 2000)
            self._generation_statuses[generation] = status

    @QtCore.pyqtSlot()
    def _apply_pending_scene_patch(self):
        if self._scene_patch_coalescer is None:
            return
        with self._scene_patch_lock:
            error = self._scene_patch_bridge_error
            self._scene_patch_bridge_error = None
            patch = self._scene_patch_coalescer.drain()
            self._scene_patch_notification_pending = False
        if error is not None:
            self.console.write(
                "{}: {}\n".format(type(error).__name__, error)
            )
            self._fail_live_scene("Invalid ScenePatch")
            return
        if patch is None:
            return
        if patch.generation != self._runner_supervisor.current_generation:
            return
        try:
            self.display_widget.apply_scene_patch(patch)
        except Exception:
            import traceback

            self.console.write(traceback.format_exc())
            self._fail_live_scene("ScenePatch presentation failed")

    def _fail_live_scene(self, message):
        if self._runner_supervisor is not None:
            self._failed_live_generation = (
                self._runner_supervisor.current_generation
            )
        if self._scene_patch_coalescer is not None:
            with self._scene_patch_lock:
                self._scene_patch_coalescer.clear()
                self._scene_patch_notification_pending = False
                self._scene_patch_bridge_error = None
        self.statusBar().showMessage(message)
        if self._runner_supervisor is not None:
            self._runner_supervisor.cancel_current()

    def closeEvent(self, event):
        if self._runner_supervisor is not None:
            self._runner_supervisor.shutdown()
        super().closeEvent(event)
        if self.notifier.isRunning():
            self.notifier.wait(1000)

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
