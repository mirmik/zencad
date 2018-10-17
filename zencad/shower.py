# coding: utf-8

import zencad

import sys
from PyQt5.QtWidgets import * #QApplication, QWidget
from PyQt5.QtCore import *
#from PyQt5.QtOpenGl import *

#import PySide

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class MainWidget(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)

class DisplayWidget(QOpenGLWidget):
	def __init__(self, view):
		QOpenGLWidget.__init__(self)
		self.view = view
		self.inited = 0

	def paintEvent(self, ev):
		print("paintEvent")
		if self.inited == 0:
			self.inited = 1
	
			self.initializeGL()
			self.resizeGL(651,551)
			self.view.set_window(self.winId())
			self.view.set_triedron()
			self.view.fit_all()
		
		self.view.redraw()
		


def show(scene):
	viewer = zencad.Viewer(scene)
	view = viewer.create_view()

	#view.see(800,800)

	app = QApplication(sys.argv)
	
	disp = DisplayWidget(view)

	w = QMainWindow()
	w.setCentralWidget(disp)
	w.resize(250, 150)
	w.move(300, 300)
	w.setWindowTitle('Simple')
	w.show()

	sys.exit(app.exec_())