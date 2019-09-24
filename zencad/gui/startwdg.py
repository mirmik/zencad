from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class StartWidget(QWidget):
	"""Виджет создающийся в начале работы в случае, если пользователь
	не указал файл, который нужно обработать.

	Задача виджета - дополнить данные для вызова основной системы"""

	def __init__(self):

		self.testbut = self.QPushButton()

		super().__init__(self)

