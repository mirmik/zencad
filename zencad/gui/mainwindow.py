import threading

import zencad.gui.actions
from zencad.gui.info_widget import InfoWidget
from PyQt5 import QtCore

from zenframe.mainwindow import ZenFrame


class MainWindow(ZenFrame, zencad.gui.actions.MainWindowActionsMixin):
    runner_message = QtCore.pyqtSignal(object)
    scene_patch_ready = QtCore.pyqtSignal()

    def __init__(self,
                 title="ZenCad",
                 restore_gui=True,
                 ):

        # Init objects
        self.info_widget = InfoWidget()
        self._pending_snapshots = {}
        self._generation_statuses = {}
        self._scene_patch_lock = threading.Lock()
        self._scene_patch_notification_pending = False
        self._scene_patch_bridge_error = None
        self._failed_live_generation = None

        super().__init__(
            title=title,
            application_name="zencad",
            restore_gui=restore_gui)

        from zencad.runtime import RunnerSupervisor, ScenePatchCoalescer

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
        self.display_widget.set_input_event_sink(self._forward_input_event)
        self.display_widget.set_viewer_event_sink(self._handle_viewer_event)

    def spawn_process(self, application_name):
        return None

    def init_central_widget(self):
        super().init_central_widget()
        from zencad.gui.display import DisplayWidget

        self.display_widget = DisplayWidget(parent=self.vsplitter)
        self.vsplitter.insertWidget(0, self.display_widget)
        self.screen_saver.hide()
        self.central_widget_layout().addWidget(self.info_widget)

    def open(self, openpath, update_texteditor=True):
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
        try:
            return self._runner_supervisor.send_input(message_type, data)
        except Exception:
            import traceback

            self.console.write(traceback.format_exc())
            self._fail_live_scene("Input transport failed")
            return False

    def _handle_viewer_event(self, event_type, data):
        if event_type in {"qmarker", "wmarker"}:
            self.info_widget.set_marker_data(
                event_type[0], data["x"], data["y"], data["z"]
            )
        elif event_type == "trackinfo":
            self.info_widget.set_tracking_info(data)

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
        self._failed_live_generation = self._runner_supervisor.current_generation
        with self._scene_patch_lock:
            self._scene_patch_coalescer.clear()
            self._scene_patch_notification_pending = False
            self._scene_patch_bridge_error = None
        self.statusBar().showMessage(message)
        self._runner_supervisor.cancel_current()

    def closeEvent(self, event):
        self._runner_supervisor.shutdown()
        super().closeEvent(event)
        if self.notifier.isRunning():
            self.notifier.wait(1000)
