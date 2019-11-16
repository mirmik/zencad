#!/usr/bin/env python3

import sys

import zencad
import zencad.gui.viewadaptor
import evalcache

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

scn = zencad.Scene()
scn.add(evalcache.unlazy(zencad.box(10)))

app = QApplication(sys.argv[:1])
zencad.opengl.init_opengl()
widget = zencad.gui.viewadaptor.DisplayWidget(scn)

widget.show()
app.exec()