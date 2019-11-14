#!/usr/bin/env python3

import zencad
import sys
import os

import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui

examples = zencad.util.examples_paths()
#print(examples)

def exec():
	pass

PyQt5.QtWidgets.QApplication.exec = exec

for epath in examples:
	cmd = sys.executable + " -m zencad --disable-show " + epath
	print(cmd)
	os.system(cmd)

	pass