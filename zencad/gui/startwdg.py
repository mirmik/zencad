import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.gui.util
import zencad.settings


class StartDialog(QDialog):
    """Виджет создающийся в начале работы в случае, если пользователь
    не указал файл, который нужно обработать.

    Задача виджета - дополнить данные для вызова основной системы"""

    def make_example_tree_nodes(self, parent, dct):
        files = dct["__files__"]

        for p in sorted([d for d in dct if d != "__files__"]):
            node = QTreeWidgetItem(parent)
            node.setText(0, str(p))
            self.make_example_tree_nodes(node, dct[p])

        for p in files:
            node = QTreeWidgetItem(parent)
            node.setText(0, str(p))

    def make_examples_tree_wdg(self):
        wdg = QTreeWidget()
        wdg.header().hide()
        examples_dict = zencad.util.examples_dict()
        self.make_example_tree_nodes(wdg, examples_dict)
        wdg.setStyleSheet(
            "QTreeWidget { background-color:transparent; color:white; border:none; }")

        return wdg

    def __init__(self):
        super().__init__()
        self.openpath = ""
        self.setWindowTitle("ZenCad")

        #self.v1_layout = QVBoxLayout()
        #self.h1_layout = QHBoxLayout()

        self.glayout = QGridLayout()

        self.examples_tree = self.make_examples_tree_wdg()
        self.examples_tree.itemDoubleClicked.connect(self.open_examples_handle)

        self.recent_scripts_wdg = QListWidget()
        for l in zencad.settings.Settings.get_recent():
            self.recent_scripts_wdg.addItem(os.path.basename(l))
        self.recent_scripts_wdg.itemDoubleClicked.connect(
            self.open_recent_handle)
        self.recent_scripts_wdg.setStyleSheet(
            "QListWidget { background-color:transparent; color:white; border:none; }")

        #self.v0_layout = QVBoxLayout()

        self.zencad_label = QLabel("ZenCad")
        fpath = os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf")
        QFontDatabase.addApplicationFont(fpath)
        font = QFont("mandarinc")
        font.setPointSize(72)
        font.setBold(True)
        self.zencad_label.setFont(font)
        self.zencad_label.setStyleSheet("QLabel{color: #C0BBFE}")

        self.h0_layout = QHBoxLayout()
        self.add_h0_button("New", self.handle_new)
        self.add_h0_button("Open", self.handle_open)
        self.add_h0_button("Manual", self.handle_help)

        self.open_recent_btn = QPushButton("Open Recent")
        self.open_example_btn = QPushButton("Open Example")
        self.open_recent_btn.setMinimumWidth(300)
        self.open_example_btn.setMinimumWidth(300)

        self.open_recent_btn.clicked.connect(self.open_recent_handle)

        self.examples_label = QLabel("Examples:")
        self.recent_label = QLabel("Recents:")

        self.examples_label.setStyleSheet("QLabel { color : white; }")
        self.recent_label.setStyleSheet("QLabel { color : white; }")

        # self.v0_layout.addLayout(self.h0_layout)
        # self.v0_layout.addWidget(self.zencad_label)

        self.not_open_next_time = QWidget()
        self.not_open_next_time_layout = QHBoxLayout()
        self.not_open_next_time_check = QCheckBox()
        self.not_open_next_time_check.stateChanged.connect(
            self.not_open_next_time_handler)
        self.not_open_next_time_layout.addStretch()
        self.not_open_next_time_label = QLabel("Не показывать этот экран")
        self.not_open_next_time_label.setStyleSheet(
            "QLabel { color : white; }")
        self.not_open_next_time_layout.addWidget(self.not_open_next_time_label)
        self.not_open_next_time_layout.addWidget(self.not_open_next_time_check)
        self.not_open_next_time.setLayout(self.not_open_next_time_layout)

        self.glayout.addWidget(self.zencad_label,		0, 0, 1, 2)
        self.glayout.addLayout(self.h0_layout, 			1, 0)
        self.glayout.addWidget(self.examples_label, 	2, 1)
        self.glayout.addWidget(self.recent_label, 		2, 0)
        self.glayout.addWidget(self.recent_scripts_wdg, 3, 0)
        self.glayout.addWidget(self.examples_tree, 		3, 1)
        self.glayout.addWidget(self.open_recent_btn, 	4, 0)
        self.glayout.addWidget(self.open_example_btn, 	4, 1)
        self.glayout.addWidget(self.not_open_next_time, 5, 0, 5, 2)

        self.setLayout(self.glayout)

    def not_open_next_time_handler(self, status):
        if status != 0:
            zencad.settings.start_screen(True)
        else:
            zencad.settings.start_screen(False)

    def paintEvent(self, ev):
        linearGrad = QLinearGradient(0, 0, self.width(), self.height())
        linearGrad.setColorAt(0, QColor(60, 0, 255/3*2))
        linearGrad.setColorAt(1, QColor(60, 0, 255/2))

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
        path = zencad.gui.util.open_file_dialog(
            self, directory=os.path.dirname(zencad.settings.Settings.get_recent()[0]))

        if len(path[0]) == 0:
            # self.reject()
            return

        self.openpath = path[0]
        self.accept()

    def handle_help(self):
        zencad.gui.util.open_online_manual()

    def open_recent_handle(self):
        index = self.recent_scripts_wdg.currentRow()
        self.openpath = zencad.settings.Settings.get_recent()[index]
        self.accept()

    def open_examples_handle(self):

        item = self.examples_tree.currentItem()
        if item.childCount() != 0:
            return

        names = []

        it = item
        while it != None:
            names.append(it.text(0))
            it = it.parent()

        names = reversed(names)
        ppath = "/".join(names)

        self.openpath = os.path.join(zencad.moduledir, "examples", ppath)
        self.accept()
