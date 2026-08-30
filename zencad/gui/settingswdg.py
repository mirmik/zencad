#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from zencad.settings import (
    MSAA_SAMPLE_OPTIONS,
    Settings,
    normalize_msaa_samples,
)
from zencad.color import Color
from zencad.gui.navigation import (
    CUSTOM_GESTURE_OPTIONS,
    NAVIGATION_SCHEME_OPTIONS,
    custom_bindings_conflict,
    normalize_custom_gesture,
    normalize_navigation_scheme,
)


class TableField(QWidget):
    def __init__(self, ltext, wdg, llen=150):
        super().__init__()
        self.label = QLabel(ltext)
        self.label.setFixedWidth(llen)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wdg = wdg
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.wdg)
        self.setLayout(self.layout)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        left, top, right, bottom = self.layout.getContentsMargins()
        spacing = self.layout.spacing()

    def restore(self):
        pass


class TextFieldChanger(QWidget):
    def __init__(self, label, path, length=200):
        super().__init__()
        self.path = path
        self.layout = QHBoxLayout()
        self.layout.addWidget(QLabel(label))
        self.edit = QLineEdit()
        self.edit.setFixedWidth(length)
        self.edit.setText(str(Settings.get(path)))
        self.layout.addWidget(self.edit)
        self.setLayout(self.layout)

    def apply(self):
        Settings.set(self.path, self.edit.text())

    def restore(self):
        pass


class Checker(QWidget):
    def __init__(self, label, path):
        super().__init__()
        self.path = path
        self.layout = QHBoxLayout()
        self.layout.addWidget(QLabel(label))
        self.check = QCheckBox()
        self.layout.addWidget(self.check)
        self.setLayout(self.layout)

    def apply(self):
        Settings.set(self.path, self.check.checkState() != 0)

    def restore(self):
        self.check.setChecked(bool(Settings.get(self.path)))


def _identity(value):
    return value


class ChoiceFieldChanger(QWidget):
    def __init__(self, label, path, choices, normalize=_identity):
        super().__init__()
        self.path = path
        self.layout = QHBoxLayout()
        self.layout.addWidget(QLabel(label))
        self.combo = QComboBox()
        for text, value in choices:
            self.combo.addItem(text, value)
        current = normalize(Settings.get(path))
        index = self.combo.findData(current)
        self.combo.setCurrentIndex(max(0, index))
        self.layout.addWidget(self.combo)
        self.setLayout(self.layout)

    def apply(self):
        Settings.set(self.path, self.combo.currentData())

    def restore(self):
        pass


class ColorChanger(QWidget):
    def __init__(self):
        super().__init__()
        values = Settings.get(["view", "default_color"])

        self.defbutton = QPushButton("Mech")
        self.defbutton.clicked.connect(self.set_default)

        labels = "RGBA"
        self.edits = [QLineEdit() for i in range(4)]
        for e in self.edits:
            e.setFixedWidth(30)

        self.layout = QHBoxLayout()
        for i in range(4):
            self.edits[i].setText(str(values[i]))
            self.layout.addWidget(TableField(
                ltext=labels[i], wdg=self.edits[i], llen=30))

        self.layout.addStretch()
        self.layout.addWidget(self.defbutton)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(QWidget())
        self.setLayout(self.layout)

    def restore(self):
        pass

    def apply(self):
        values = tuple([float(e.text()) for e in self.edits])
        # if values != Settings.get(["view", "default_color"]):
        #    print("You should reevaluate script for color applying")
        Settings.set(["view", "default_color"], values)

    def set_default(self):
        self.edits[0].setText(str(round(Color.mech.r, 5)))
        self.edits[1].setText(str(round(Color.mech.g, 5)))
        self.edits[2].setText(str(round(Color.mech.b, 5)))
        self.edits[3].setText(str(round(Color.mech.a, 5)))


class SettingsWidget(QDialog):
    """Виджет настроек системы"""

    def __init__(self):
        super().__init__()

        self.ok_button = QPushButton("Ok")
        self.cancel_button = QPushButton("Cancel")
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.ok_button)
        self.hlayout.addWidget(self.cancel_button)

        self.default_color_edit = ColorChanger()
        self.texteditor_edit = TextFieldChanger(
            path=["gui", "text_editor"], label="Text editor command:")
        self.marker_size_edit = TextFieldChanger(
            path=["markers", "size"], label="Marker size:")
        self.cache_directory_edit = TextFieldChanger(
            path=["cache", "directory"], label="Cache directory:")
        self.cache_enabled_edit = Checker(
            "Enable disk cache:",
            ["cache", "enabled"],
        )
        self.chordial_deflection_edit = TextFieldChanger(
            path=["view", "default_chordial_deviation"], label="Chordial deflection:")
        self.msaa_edit = ChoiceFieldChanger(
            label="MSAA:",
            path=["view", "msaa_samples"],
            choices=[
                ("Off" if samples == 0 else "{}×".format(samples), samples)
                for samples in MSAA_SAMPLE_OPTIONS
            ],
            normalize=normalize_msaa_samples,
        )
        self.navigation_scheme_edit = ChoiceFieldChanger(
            label="Navigation:",
            path=["view", "navigation_scheme"],
            choices=NAVIGATION_SCHEME_OPTIONS,
            normalize=normalize_navigation_scheme,
        )
        self.navigation_rotate_edit = ChoiceFieldChanger(
            label="Custom rotate:",
            path=["view", "navigation_rotate"],
            choices=CUSTOM_GESTURE_OPTIONS,
            normalize=lambda value: normalize_custom_gesture(value, "left"),
        )
        self.navigation_pan_edit = ChoiceFieldChanger(
            label="Custom pan:",
            path=["view", "navigation_pan"],
            choices=CUSTOM_GESTURE_OPTIONS,
            normalize=lambda value: normalize_custom_gesture(value, "middle"),
        )
        self.navigation_zoom_edit = ChoiceFieldChanger(
            label="Custom zoom:",
            path=["view", "navigation_zoom"],
            choices=CUSTOM_GESTURE_OPTIONS,
            normalize=normalize_custom_gesture,
        )
        self.navigation_invert_wheel_edit = Checker(
            "Invert wheel zoom:",
            ["view", "navigation_invert_wheel"],
        )
        self.navigation_invert_orbit_edit = Checker(
            "Invert orbit direction:",
            ["view", "navigation_invert_orbit"],
        )

        self.appliers = []
        self.vlayout = QVBoxLayout()

        def append(obj):
            self.appliers.append(obj)
            self.vlayout.addWidget(obj)

        append(self.texteditor_edit)
        append(self.default_color_edit)
        append(self.marker_size_edit)
        append(self.cache_directory_edit)
        append(self.cache_enabled_edit)
        append(self.chordial_deflection_edit)
        append(self.msaa_edit)
        append(self.navigation_scheme_edit)
        append(self.navigation_rotate_edit)
        append(self.navigation_pan_edit)
        append(self.navigation_zoom_edit)
        append(self.navigation_invert_wheel_edit)
        append(self.navigation_invert_orbit_edit)

        self.vlayout.addLayout(self.hlayout)

        for a in self.appliers:
            a.restore()

        self.navigation_scheme_edit.combo.currentIndexChanged.connect(
            self.update_navigation_controls
        )
        self.update_navigation_controls()

        self.ok_button.clicked.connect(self.ok_handle)
        self.cancel_button.clicked.connect(self.cancel_handle)

        self.setLayout(self.vlayout)

    def save_all(self):
        for a in self.appliers:
            a.apply()
        Settings.store()

    def update_navigation_controls(self):
        custom = self.navigation_scheme_edit.combo.currentData() == "custom"
        self.navigation_rotate_edit.setEnabled(custom)
        self.navigation_pan_edit.setEnabled(custom)
        self.navigation_zoom_edit.setEnabled(custom)

    def navigation_settings_are_valid(self):
        if self.navigation_scheme_edit.combo.currentData() != "custom":
            return True
        bindings = {
            "rotate": self.navigation_rotate_edit.combo.currentData(),
            "pan": self.navigation_pan_edit.combo.currentData(),
            "zoom": self.navigation_zoom_edit.combo.currentData(),
        }
        if not custom_bindings_conflict(bindings):
            return True
        QMessageBox.warning(
            self,
            "Navigation conflict",
            "Rotate, pan, and zoom cannot use the same mouse gesture.",
        )
        return False

    def cache_settings_are_valid(self):
        from zencad.cache_config import (
            normalize_cache_directory,
            prepare_cache_directory,
        )

        try:
            directory = normalize_cache_directory(
                self.cache_directory_edit.edit.text()
            )
            if self.cache_enabled_edit.check.isChecked():
                prepare_cache_directory(directory)
        except (OSError, ValueError, RuntimeError) as exception:
            QMessageBox.warning(
                self,
                "Invalid cache configuration",
                str(exception),
            )
            return False
        return True

    def ok_handle(self):
        if not self.navigation_settings_are_valid():
            return
        if not self.cache_settings_are_valid():
            return
        self.save_all()
        self.accept()

    def cancel_handle(self):
        self.reject()


def doit():
    import sys
    app = QApplication(sys.argv[1:])
    Settings.restore()
    wdg = SettingsWidget()
    wdg.exec()


if __name__ == "__main__":
    doit()
