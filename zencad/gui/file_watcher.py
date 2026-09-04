"""Debounced source-file watcher owned by the Qt event loop."""

from pathlib import Path

from PyQt5 import QtCore


class FileWatcher(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, debounce_ms=500):
        super().__init__(parent)
        self._enabled = True
        self._targets = set()
        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._file_changed)

        self._debounce = QtCore.QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self._emit_changed)

    def clear(self):
        watched = self._watcher.files()
        if watched:
            self._watcher.removePaths(watched)
        self._targets.clear()
        self._debounce.stop()

    def add_target(self, path):
        path = str(Path(path).resolve())
        self._targets.add(path)
        if Path(path).is_file() and path not in self._watcher.files():
            self._watcher.addPath(path)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if not self._enabled:
            self._debounce.stop()

    def control_lock(self):
        self.set_enabled(False)

    def control_unlock(self):
        self.set_enabled(True)

    def stop(self):
        self.clear()
        self._enabled = False

    @QtCore.pyqtSlot(str)
    def _file_changed(self, _path):
        if self._enabled:
            self._debounce.start()

    @QtCore.pyqtSlot()
    def _emit_changed(self):
        # Atomic saves replace the inode and make QFileSystemWatcher forget the
        # path. Re-arm every surviving target before notifying MainWindow.
        watched = set(self._watcher.files())
        for path in self._targets:
            if Path(path).is_file() and path not in watched:
                self._watcher.addPath(path)
        if self._enabled:
            self.changed.emit()
