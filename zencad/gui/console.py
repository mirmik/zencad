"""Thread-safe output console for the ZenCad application window."""

import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class ConsoleWidget(QtWidgets.QTextEdit):
    append_text = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mirror_stdout=True):
        super().__init__(parent)
        self._stdout = sys.stdout if mirror_stdout else None
        if mirror_stdout:
            sys.stdout = self

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(245, 245, 245))
        self.setPalette(palette)
        font = QtGui.QFont("Monospace", 10)
        font.setStyleHint(QtGui.QFont.Monospace)
        self.setFont(font)
        self.setReadOnly(True)
        self.setMinimumHeight(120)
        self.append_text.connect(self._append_text, QtCore.Qt.QueuedConnection)

    def write(self, data):
        text = str(data)
        self.append_text.emit(text)
        if self._stdout is not None:
            self._stdout.write(text)
            self._stdout.flush()

    def flush(self):
        if self._stdout is not None:
            self._stdout.flush()

    def restore_stdout(self):
        if self._stdout is not None and sys.stdout is self:
            sys.stdout = self._stdout

    def clear(self):
        self.setPlainText("")

    @QtCore.pyqtSlot(str)
    def _append_text(self, data):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(data)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
