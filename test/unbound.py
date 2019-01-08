#!/usr/bin/env python3

import zencad
import zencad.viewadaptor
import zencad.unbound

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

scn = zencad.Scene()

scn.add(zencad.box(20,20,20).unlazy())

zencad.show(scn)
