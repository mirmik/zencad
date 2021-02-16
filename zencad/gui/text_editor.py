#!/usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

import time


def format(color, style=""):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    "keyword": QColor(255, 0, 0),
    "operator": format("red"),
    "brace": QColor(255, 255, 255),
    "defclass": QColor(120, 255, 0),
    "string": QColor(231, 219, 116),
    "string2": format("darkMagenta"),
    "comment": QColor(80, 80, 80),
    "self": QColor(255, 120, 0),
    "numbers": QColor(255, 0, 255),
}


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """

    # Python keywords
    keywords = [
        "and",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "exec",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "not",
        "or",
        "pass",
        "print",
        "raise",
        "return",
        "try",
        "while",
        "yield",
        "None",
        "True",
        "False",
    ]

    # Python operators
    operators = [
        "=",
        # Comparison
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        # Arithmetic
        "\+",
        "-",
        "\*",
        "/",
        "//",
        "\%",
        "\*\*",
        # In-place
        "\+=",
        "-=",
        "\*=",
        "/=",
        "\%=",
        # Bitwise
        "\^",
        "\|",
        "\&",
        "\~",
        ">>",
        "<<",
    ]

    # Python braces
    braces = ["\{", "\}", "\(", "\)", "\[", "\]"]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES["string2"])
        self.tri_double = (QRegExp('"""'), 2, STYLES["string2"])

        rules = []

        # Keyword, operator, and brace rules
        rules += [
            (r"\b%s\b" % w, 0, STYLES["keyword"]) for w in PythonHighlighter.keywords
        ]
        rules += [
            (r"%s" % o, 0, STYLES["operator"]) for o in PythonHighlighter.operators
        ]
        rules += [(r"%s" % b, 0, STYLES["brace"])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r"\bself\b", 0, STYLES["self"]),
            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES["string"]),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES["string"]),
            # 'def' followed by an identifier
            (r"\bdef\b\s*(\w+)", 1, STYLES["defclass"]),
            # 'class' followed by an identifier
            (r"\bclass\b\s*(\w+)", 1, STYLES["defclass"]),
            # From '#' until a newline
            (r"#[^\n]*", 0, STYLES["comment"]),
            # Numeric literals
            (r"\b[+-]?[0-9]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b",
             0, STYLES["numbers"]),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class LineNumberArea(QWidget):
    def __init__(self, editor):
        QWidget.__init__(self, editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class TextEditor(QPlainTextEdit):
    def __init__(self):
        self.base_color = QColor(40, 41, 35)
        self.lines_numbers_border = 10
        self.last_save = time.time() - 1

        QPlainTextEdit.__init__(self)
        pallete = self.palette()
        pallete.setColor(QPalette.Base, self.base_color)
        pallete.setColor(QPalette.Text, QColor(255, 255, 255))
        self.setPalette(pallete)
        self.highlighter = PythonHighlighter(self.document())
        self.rewrite = None
        self.edited = None

        self.lineNumberArea = LineNumberArea(self)

        font = QFont()
        font.setFamily("Monospace")
        font.setPointSize(10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        metrics = QFontMetrics(font)
        self.setTabStopWidth(metrics.width("    "))

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        # self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth()

    def save(self):
        self.last_save = time.time()
        try:
            f = open(self.edited, "w")
            self.rewrite = self.edited
        except IOError as e:
            print("cannot open {} for write: {}".format(self.edited, e))
            return
        f.write(self.toPlainText())
        f.close()

    def save_as(self, path):
        try:
            f = open(path, "w")
            self.rewrite = path
            self.edited = path
        except IOError as e:
            print("cannot open {} for write: {}".format(self.edited, e))
            return
        f.write(self.toPlainText())
        f.close()

    def open(self, path):
        if path == self.edited and path == self.rewrite:
            self.rewrite = None
            return
        self.edited = path
        self.update_text_field()

    def update_text_field(self):
        filetext = open(self.edited).read()
        self.setPlainText(filetext)

    def reopen(self):
        # Если сохранение осуществелено изнутри, предотвращаем обновление
        # редактора. Иначе, обновляем изходя из изменённых данных.
        if time.time() - self.last_save < 0.5:
            pass
        else:
            self.update_text_field()

    def keyPressEvent(self, event):
        QPlainTextEdit.keyPressEvent(self, event)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        rect = QRect(
            event.rect().x(),
            event.rect().y(),
            event.rect().width(),
            event.rect().height())
        painter.fillRect(rect, self.base_color)
        #painter.fillRect(event.rect(), Qt.red)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = qRound(self.blockBoundingGeometry(
            block).translated(self.contentOffset()).top())
        bottom = top + qRound(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.gray)
                painter.drawText(0, top, self.lineNumberArea.width() - self.lines_numbers_border,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + qRound(self.blockBoundingRect(block).height())
            blockNumber += 1

    def updateLineNumberAreaWidth(self):
        self.setViewportMargins(
            self.lineNumberAreaWidth() + self.lines_numbers_border, 0, 0, 0)

    def resizeEvent(self, e):
        QPlainTextEdit.resizeEvent(self, e)
        cr = self.contentsRect()
        self.updateLineNumberAreaWidth()

        argrect = QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(
        ) + self.lines_numbers_border, cr.height())

        self.lineNumberArea.setGeometry(argrect)

    def lineNumberAreaWidth(self):
        digits = 1
        maxim = max(1, self.blockCount())
        while maxim >= 10:
            maxim /= 10
            digits += 1

        space = 3 + self.fontMetrics().width('9'[0]) * digits

        return space
