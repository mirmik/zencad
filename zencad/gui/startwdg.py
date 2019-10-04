from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.gui.util
import os

class StartDialog(QDialog):
	"""Виджет создающийся в начале работы в случае, если пользователь
	не указал файл, который нужно обработать.

	Задача виджета - дополнить данные для вызова основной системы"""

	def __init__(self):
		super().__init__()
		self.openpath = ""
		self.setWindowTitle("ZenCad")

		#self.v1_layout = QVBoxLayout()
		#self.h1_layout = QHBoxLayout()

		self.glayout = QGridLayout()

		self.examples_tree = QTreeWidget()
		self.examples_tree.header().hide()
		item = QTreeWidgetItem(self.examples_tree)
		item.setText(0,"UNDER_CONSTRUCT")

		self.recent_scripts_wdg = QListWidget()
		self.recent_scripts_wdg.addItem("UNDER_CONSTRUCT")  

		#self.v0_layout = QVBoxLayout()
		
		self.zencad_label = QLabel("ZenCad")
		fpath = os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf")
		QFontDatabase.addApplicationFont(fpath)
		font = QFont("mandarinc")
		font.setPointSize(72)
		font.setBold(True)
		self.zencad_label.setFont(font)
		self.zencad_label.setStyleSheet("QLabel{color: #C0BBFE}");
		
		self.h0_layout = QHBoxLayout()
		self.add_h0_button("New", self.handle_new)
		self.add_h0_button("Open", self.handle_open)
		self.add_h0_button("Help", self.handle_help)

		self.open_recent_btn = QPushButton("Open Recent")
		self.open_example_btn = QPushButton("Open Example")
		self.open_recent_btn.setMinimumWidth(300)
		self.open_example_btn.setMinimumWidth(300)

		#self.v0_layout.addLayout(self.h0_layout)
		#self.v0_layout.addWidget(self.zencad_label)

		self.glayout.addWidget(self.zencad_label,		0,0, 1,2)
		self.glayout.addLayout(self.h0_layout, 			1,0)
		self.glayout.addWidget(self.examples_tree, 		1,1, 2,1)
		self.glayout.addWidget(self.recent_scripts_wdg, 2,0)
		self.glayout.addWidget(self.open_recent_btn, 	3,0)
		self.glayout.addWidget(self.open_example_btn, 	3,1)

		self.setLayout(self.glayout)

	def paintEvent(self, ev):
		linearGrad = QLinearGradient(0, 0, self.width(), self.height())
		linearGrad.setColorAt(0, Qt.blue)
		linearGrad.setColorAt(1, Qt.darkBlue)
 
		palette = self.palette()
		palette.setBrush(QPalette.Background, linearGrad)
		self.setPalette(palette)

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

		if len(path[0]) == 0:
			#self.reject()
			return

		self.openpath = path[0]
		self.accept()

	def handle_help(self):
		zencad.gui.util.open_online_manual()