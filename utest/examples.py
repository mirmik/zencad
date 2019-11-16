#!/usr/bin/env python3

import zencad
import sys
import os
import subprocess

import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui

examples = zencad.util.examples_paths(root="../zencad/examples")

if "TRAVIS_OS_NAME" in os.environ:
	print("Travis. Filter examples.")
	examples = [ e for e in examples if not "Embeded" in e ]
	examples = [ e for e in examples if not "Integration" in e ]


for epath in examples:
	cmd = sys.executable + " -m zencad --disable-show " + epath
	print(cmd)
	
	exit_code = subprocess.call(cmd, shell=True)
	if exit_code != 0:
		print(exit_code)
		raise Exception("Error in example {0}".format(epath))