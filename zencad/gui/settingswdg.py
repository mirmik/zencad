#!/usr/bin/env python3 

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.gui.settings

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

		self.layout.setContentsMargins(0,0,0,0)
		self.layout.setSpacing(5)
		left, top, right, bottom = self.layout.getContentsMargins()
		spacing = self.layout.spacing()
		#self.setFixedWidth(llen + self.wdg.width() + right + spacing)

class LineEdit(QLineEdit):
	def __init__(self, deftext="", length=200):
		super().__init__()
		self.setFixedWidth(length)
		self.setText(deftext)

class ColorChanger(QWidget):
	def __init__(self, values):
		super().__init__()
		labels = "RGBA"
		self.edits = [ LineEdit(length=30) for i in range(4) ]

		self.layout = QHBoxLayout()
		for i in range(4):
			self.edits[i].setText(str(values[i]))
			self.layout.addWidget(TableField(ltext=labels[i], wdg=self.edits[i], llen=30))

		self.layout.setContentsMargins(0,0,0,0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)

class SettingsWidget(QDialog):
	"""Виджет настроек системы"""

	def __init__(self):
		super().__init__()

		settings = zencad.gui.settings.Settings()

		self.vlayout = QVBoxLayout()
		self.vlayout.addWidget(TableField(ltext="Home directory", wdg=LineEdit()))
		self.vlayout.addWidget(TableField(ltext="Text editor command", wdg=LineEdit(deftext=settings.get_settings()["gui"]["text_editor"])))
		self.vlayout.addWidget(TableField(ltext="Default color", wdg=ColorChanger(values=settings.get_default_color())))

		self.setLayout(self.vlayout)


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv[1:])
	wdg = SettingsWidget()
	wdg.exec()


