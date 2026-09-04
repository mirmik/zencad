"""Small Python editor used by the ZenCad application window."""

import keyword
from pathlib import Path
import time

from PyQt5 import QtCore, QtGui, QtWidgets


def _text_format(color, bold=False, italic=False):
    result = QtGui.QTextCharFormat()
    result.setForeground(QtGui.QColor(color))
    if bold:
        result.setFontWeight(QtGui.QFont.Bold)
    if italic:
        result.setFontItalic(True)
    return result


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """Lightweight syntax highlighting without deprecated QRegExp APIs."""

    def __init__(self, document):
        super().__init__(document)
        keyword_format = _text_format("#ff5555", bold=True)
        builtin_format = _text_format("#8be9fd")
        string_format = _text_format("#f1fa8c")
        comment_format = _text_format("#6272a4", italic=True)
        number_format = _text_format("#ff79c6")
        definition_format = _text_format("#50fa7b", bold=True)

        self.rules = [
            (
                QtCore.QRegularExpression(
                    r"\b(?:{})\b".format("|".join(keyword.kwlist))
                ),
                keyword_format,
            ),
            (
                QtCore.QRegularExpression(r"\b(?:True|False|None|self)\b"),
                builtin_format,
            ),
            (
                QtCore.QRegularExpression(
                    r"\b(?:0[xX][0-9A-Fa-f]+|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)\b"
                ),
                number_format,
            ),
            (
                QtCore.QRegularExpression(r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"),
                string_format,
            ),
            (QtCore.QRegularExpression(r"#[^\n]*"), comment_format),
            (
                QtCore.QRegularExpression(r"\b(?:def|class)\s+([A-Za-z_]\w*)"),
                definition_format,
                1,
            ),
        ]

    def highlightBlock(self, text):
        for rule in self.rules:
            expression, text_format = rule[:2]
            capture = rule[2] if len(rule) == 3 else 0
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(
                    match.capturedStart(capture),
                    match.capturedLength(capture),
                    text_format,
                )


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QtWidgets.QPlainTextEdit):
    """A focused editor with the file operations expected by MainWindow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edited = None
        self._rewritten_path = None
        self._last_save = 0.0

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(40, 41, 35))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(245, 245, 245))
        self.setPalette(palette)

        font = QtGui.QFont("Monospace", 10)
        font.setStyleHint(QtGui.QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(QtGui.QFontMetricsF(font).horizontalAdvance("    "))

        self.highlighter = PythonHighlighter(self.document())
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width()

    def open(self, path):
        path = str(Path(path).resolve())
        if path == self.edited and path == self._rewritten_path:
            self._rewritten_path = None
            return
        self.edited = path
        self.reopen(force=True)

    def save(self):
        if self.edited is None:
            raise ValueError("No file is open")
        self._write(self.edited)

    def save_as(self, path):
        self.edited = str(Path(path).resolve())
        self._write(self.edited)

    def _write(self, path):
        Path(path).write_text(self.toPlainText(), encoding="utf-8")
        self._last_save = time.monotonic()
        self._rewritten_path = path
        self.document().setModified(False)

    def reopen(self, force=False):
        if self.edited is None:
            return
        if not force and time.monotonic() - self._last_save < 0.75:
            return
        self.setPlainText(Path(self.edited).read_text(encoding="utf-8"))
        self.document().setModified(False)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _count=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                rect.y(),
                self.line_number_area.width(),
                rect.height(),
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        contents = self.contentsRect()
        self.line_number_area.setGeometry(
            QtCore.QRect(
                contents.left(),
                contents.top(),
                self.line_number_area_width(),
                contents.height(),
            )
        )

    def paint_line_numbers(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(40, 41, 35))
        painter.setPen(QtGui.QColor(120, 120, 120))

        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight,
                    str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            number += 1
