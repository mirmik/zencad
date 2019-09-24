from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import tempfile


def create_temporary_file(zencad_template=False):
	path = tempfile.mktemp(".py")
	
	if zencad_template:
		f = open(path, "w")
		f.write(
			"#!/usr/bin/env python3\n#coding: utf-8\n\nfrom zencad import *\n\nm=box(10)\ndisp(m)\n\nshow()\n"
		)
		f.close()

	return path

def open_file_dialog(parent):
	filters = "*.py;;*.*"
	defaultFilter = "*.py"

	#startpath = (
	#	QDir.currentPath()
	#	if self.current_opened is None
	#	else os.path.dirname(self.current_opened)
	#)

	path = QFileDialog.getOpenFileName(
		parent, "Open File", "", filters, defaultFilter
	)
	print(path)

	return path