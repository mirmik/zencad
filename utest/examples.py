#!/usr/bin/env python3

import zencad
import sys
import os
import subprocess

import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui

examples = zencad.util.examples_paths()

for epath in examples:
	cmd = sys.executable + " -m zencad --disable-show " + epath
	print(cmd)
	x = subprocess.check_output(cmd.split())
	if x != 0:
		raise Exception("Error in example {0}".format(epath))