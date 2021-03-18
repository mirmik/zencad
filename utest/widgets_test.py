#!/usr/bin/env python3
# coding:utf-8

import unittest
import zencad

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from zencad.gui.settingswdg import SettingsWidget

qapp = QApplication([])


class WidgetsTest(unittest.TestCase):
    def test_segment_probe(self):
        settings = SettingsWidget()
