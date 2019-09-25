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

		self.add_h0_button("New", self.handle_new)
		self.add_h0_button("Open", self.handle_open)
		self.add_h0_button("Help", self.handle_help)

		self.setLayout(self.h0_layout)

	def add_h0_button(self, text, handle):
		btn = QPushButton(text)
		btn.clicked.connect(handle)
		self.h0_layout.addWidget(btn)

	def handle_new(self):
		self.openpath = zencad.gui.util.create_temporary_file(
			zencad_template=True)
		self.accept()

	def handle_open(self):
		path = zencad.gui.util.open_file_dialog(self)

		if len(path[0]) == 0 or path[0][0] != '\\':
			self.reject()
			return

		self.openpath = path[0]
		self.accept()

	def handle_help(self):
		zencad.gui.util.open_online_manual()