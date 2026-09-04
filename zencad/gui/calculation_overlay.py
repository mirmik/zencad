"""Non-invasive calculation overlay for the persistent OCCT viewer."""

from PyQt5 import QtCore, QtGui, QtWidgets


class CalculationOverlay(QtWidgets.QWidget):
    """Dim the last viewer frame and present evalcache progress."""

    def __init__(self, viewer):
        super().__init__(viewer)
        self._viewer = viewer
        self._active = False
        self._background = QtGui.QPixmap()
        self._title = "Calculating model…"
        self._tree_objects = None
        self._tree_root = None
        self._to_load = None
        self._to_evaluate = None
        self._initial_work = None
        self._operation = None
        self._object_name = None
        self._pulse = 0

        self.setObjectName("calculationOverlay")
        self.setAccessibleName("Model calculation progress")
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, False)
        self.setAutoFillBackground(False)
        self.hide()

        self._pulse_timer = QtCore.QTimer(self)
        self._pulse_timer.setInterval(350)
        self._pulse_timer.timeout.connect(self._advance_pulse)
        viewer.installEventFilter(self)

    @property
    def active(self):
        return self._active

    @property
    def progress_lines(self):
        lines = []
        if self._tree_objects is not None:
            tree = "Evaluation tree: {} objects".format(self._tree_objects)
            if self._tree_root:
                tree += " · root {}".format(self._tree_root)
            lines.append(tree)
        if self._to_load is not None or self._to_evaluate is not None:
            lines.append(
                "Remaining: {} to load · {} to evaluate".format(
                    self._to_load if self._to_load is not None else "?",
                    (
                        self._to_evaluate
                        if self._to_evaluate is not None
                        else "?"
                    ),
                )
            )
        if self._operation or self._object_name:
            operation = {
                "load": "Loading from cache",
                "evaluate": "Evaluating",
                "memory": "Preparing",
            }.get(self._operation, "Processing")
            if self._object_name:
                operation += ": {}".format(self._object_name)
            lines.append(operation)
        return lines

    def begin(self, capture_background=True):
        if capture_background and not self._active:
            self._background = self._capture_viewer()
        elif not capture_background:
            self._background = QtGui.QPixmap()

        self._title = "Calculating model…"
        self._tree_objects = None
        self._tree_root = None
        self._to_load = None
        self._to_evaluate = None
        self._initial_work = None
        self._operation = None
        self._object_name = None
        self._pulse = 0
        self._active = True
        self.setGeometry(self._viewer.rect())
        self.show()
        self.raise_()
        self._pulse_timer.start()
        self.update()

    def finish(self):
        self._active = False
        self._pulse_timer.stop()
        self.hide()
        self._background = QtGui.QPixmap()

    def set_phase(self, text):
        if text:
            self._title = str(text)
            self.update()

    def update_progress(self, payload):
        phase = payload.get("phase")
        if phase:
            self.set_phase({
                "evaluating": "Calculating model…",
                "finalizing": "Finalizing scene…",
            }.get(phase, str(phase).replace("_", " ").capitalize()))

        subcmd = payload.get("subcmd")
        if subcmd == "newtree":
            self._tree_objects = payload.get("len")
            root = payload.get("root")
            self._tree_root = str(root)[:8] if root else None
        elif subcmd == "progress":
            self._to_load = payload.get("toload")
            self._to_evaluate = payload.get("toeval")
            if isinstance(self._to_load, int) and isinstance(
                self._to_evaluate, int
            ):
                remaining = self._to_load + self._to_evaluate
                if self._initial_work is None or remaining > self._initial_work:
                    self._initial_work = remaining
            if "operation" in payload:
                self._operation = payload.get("operation")
            if "object" in payload:
                self._object_name = payload.get("object")
        self.update()

    def eventFilter(self, watched, event):
        if watched is self._viewer and event.type() in {
            QtCore.QEvent.Resize,
            QtCore.QEvent.Show,
        }:
            self.setGeometry(self._viewer.rect())
            if self._active:
                self.raise_()
        return super().eventFilter(watched, event)

    def _capture_viewer(self):
        if not self._viewer.isVisible():
            return QtGui.QPixmap()
        screen = self._viewer.screen()
        if screen is None:
            screen = QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return QtGui.QPixmap()
        return screen.grabWindow(int(self._viewer.winId()))

    def _advance_pulse(self):
        self._pulse = (self._pulse + 1) % 4
        if self._active:
            self.raise_()
            self.update()

    def _progress_fraction(self):
        if not self._initial_work:
            return None
        if not isinstance(self._to_load, int) or not isinstance(
            self._to_evaluate, int
        ):
            return None
        remaining = self._to_load + self._to_evaluate
        return max(0.0, min(1.0, 1.0 - remaining / self._initial_work))

    def paintEvent(self, event):
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        if self._background.isNull():
            painter.fillRect(self.rect(), QtGui.QColor(18, 20, 24))
        else:
            painter.drawPixmap(self.rect(), self._background)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 205))

        content_width = min(620, max(260, self.width() - 64))
        left = (self.width() - content_width) // 2
        title_font = QtGui.QFont(self.font())
        title_font.setPointSize(17)
        title_font.setBold(True)
        detail_font = QtGui.QFont(self.font())
        detail_font.setPointSize(11)

        lines = self.progress_lines
        block_height = 50 + len(lines) * 27 + 28
        top = max(24, (self.height() - block_height) // 2)

        painter.setPen(QtGui.QColor(245, 245, 245))
        painter.setFont(title_font)
        title = self._title + "." * self._pulse
        painter.drawText(
            QtCore.QRect(left, top, content_width, 34),
            QtCore.Qt.AlignCenter,
            title,
        )

        painter.setFont(detail_font)
        painter.setPen(QtGui.QColor(210, 214, 220))
        y = top + 45
        for line in lines:
            painter.drawText(
                QtCore.QRect(left, y, content_width, 24),
                QtCore.Qt.AlignCenter,
                line,
            )
            y += 27

        bar_rect = QtCore.QRect(left, y + 8, content_width, 6)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(78, 82, 90))
        painter.drawRoundedRect(bar_rect, 3, 3)
        fraction = self._progress_fraction()
        if fraction is not None:
            filled = QtCore.QRect(bar_rect)
            filled.setWidth(round(bar_rect.width() * fraction))
            painter.setBrush(QtGui.QColor(137, 90, 190))
            painter.drawRoundedRect(filled, 3, 3)

