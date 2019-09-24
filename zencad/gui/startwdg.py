from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.gui.util

class StartDialog(QDialog):
	"""Виджет создающийся в начале работы в случае, если пользователь
	не указал файл, который нужно обработать.

	Задача виджета - дополнить данные для вызова основной системы"""

	def __init__(self):
		super().__init__()
		self.openpath = ""

		self.h0_layout = QHBoxLayout()
		self.button_create_new = QPushButton("New")
		self.button_open = QPushButton("Open")

		self.h0_layout.addWidget(self.button_create_new)
		self.h0_layout.addWidget(self.button_open)
		self.setLayout(self.h0_layout)

		self.init_signals()

	def init_signals(self):
		self.button_create_new.clicked.connect(self.handle_create_new)
		self.button_open.clicked.connect(self.handle_open)

	def handle_create_new(self):
		self.openpath = zencad.gui.util.create_temporary_file(
			zencad_template=True)
		self.accept()

	def handle_open(self):
		path = zencad.gui.util.open_file_dialog(self)

		print(path[0])
		print(len(path[0]))
		if len(path[0]) == 0 or path[0][0] != '\\':
			self.reject()
			return

		self.openpath = path[0]
		self.accept()