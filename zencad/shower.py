# coding: utf-8

import zencad

import sys
from PyQt5.QtWidgets import * #QApplication, QWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
#from PyQt5.QtOpenGl import *

#import PySide

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class MainWidget(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)

class DisplayWidget(QOpenGLWidget):
#class DisplayWidget(QWidget):
	def __init__(self, arg):
		QOpenGLWidget.__init__(self)
#		QWidget.__init__(self)
		
		#self.initializeGL()
		#self.resizeGL(800, 800)

		self.scene = arg
		self.visinit()

		self.setBackgroundRole( QPalette.NoRole );
		self.setAttribute(Qt.WA_PaintOnScreen, True); 
		#self.setAttribute(Qt.WA_NoSystemBackground, True); 
		
		self.inited = 0

	def visinit(self):
		print("visinit")
		self.viewer = zencad.Viewer(self.scene)
		self.view = self.viewer.create_view()

		self.view.set_triedron()
		self.view.set_window(self.winId())
		self.view.fit_all()


	def paintEvent(self, ev):
		print("paintEvent")		
		self.view.redraw()

	def showEvent(self, ev):
		print("showEvent")
		self.view.redraw()		

	def resizeEvent(self, ev):
		print("resizeEvent")
		self.view.must_be_resized()

	
	#def paintEngine(self):
	#	return None;

		


def show(scene):

	#view.see(800,800)

	app = QApplication(sys.argv)

	fmt = QSurfaceFormat()
	fmt.setDepthBufferSize(24)
	fmt.setStencilBufferSize(8)
	fmt.setVersion(3, 2)
	fmt.setProfile(QSurfaceFormat.CoreProfile)
	QSurfaceFormat.setDefaultFormat(fmt); # must be called before the widget or its parent window gets shown

	mw = QMainWindow();	
	disp = DisplayWidget(scene)
	mw.setCentralWidget(disp)

	#w = QWindow()
	#ww = QWidget.createWindowContainer(w)


	#viewer = zencad.Viewer(scene)
	#view = viewer.create_view()
	#view.set_window(w.winId())
	#view.set_triedron()
	#view.fit_all()
#
	#view.set_window(w.winId())
		
	#w = QMainWindow()
	#w.setCentralWidget(disp)
	#w.resize(250, 150)
	#w.move(300, 300)
	#w.setWindowTitle('Simple')
	#w.show()

	mw.resize(800,600)
	mw.show()

	#w.show()

	sys.exit(app.exec_())