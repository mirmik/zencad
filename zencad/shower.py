# coding: utf-8

import zencad

import sys
import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PIL import Image
import numpy as np

#from OpenGL.GL import *
#from OpenGL.GLUT import *
#from OpenGL.GLU import *

import math

class MainWidget(QMainWindow):
	def __init__(self, dispw):
		QMainWindow.__init__(self)
		self.dispw = dispw

		self.setWindowTitle("zenwidget");
		#self.setWindowIcon(QIcon(":/industrial-robot.svg"));

		self.createActions();
		self.createMenus();
		self.createToolbars();

	def createActions(self):
		self.mExitAction = QAction(self.tr("Exit"), self)
		self.mExitAction.setShortcut(self.tr("Ctrl+Q"))
		self.mExitAction.setStatusTip(self.tr("Exit the application"))
		self.mExitAction.triggered.connect(self.close)
	
		self.mStlExport = QAction(self.tr("Export STL..."), self)
		self.mStlExport.setStatusTip(self.tr("Export file with external STL-Mesh format"))
		self.mStlExport.triggered.connect(self.exportStlAction);
	
		self.mScreen = QAction(self.tr("Screenshot..."), self)
		self.mScreen.setStatusTip(self.tr("Do screen"))
		self.mScreen.triggered.connect(self.screenshotAction)
	
		self.mAboutAction = QAction(self.tr("About"), self)
		self.mAboutAction.setStatusTip(self.tr("About the application"))
		self.mAboutAction.triggered.connect(self.aboutAction)
	
		self.mReset = QAction(self.tr("Reset"), self)
		self.mReset.setStatusTip(self.tr("Reset"))
		self.mReset.triggered.connect(self.resetAction)

		self.mAutoscale = QAction(self.tr("Autoscale"), self)
		self.mAutoscale.setStatusTip(self.tr("Autoscale"))
		self.mAutoscale.triggered.connect(self.autoscaleAction)
	
		self.mOrient1 = QAction(self.tr("Orient1"), self)
		self.mOrient1.setStatusTip(self.tr("Orient1"))
		self.mOrient1.triggered.connect(self.orient1)
	
		self.mOrient2 = QAction(self.tr("Orient2"), self)
		self.mOrient2.setStatusTip(self.tr("Orient2"))
		self.mOrient2.triggered.connect(self.orient2)

	def createMenus(self):
		self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.mFileMenu.addAction(self.mStlExport)
		self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)
	
		self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
		self.mNavigationMenu.addAction(self.mReset)
		self.mNavigationMenu.addAction(self.mAutoscale)
		self.mNavigationMenu.addAction(self.mOrient1)
		self.mNavigationMenu.addAction(self.mOrient2)
	
		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.mHelpMenu.addAction(self.mAboutAction)
		
	def createToolbars(self):
		pass

	def exportStlAction(self):
		pass
#		pyservoce.to_stl(self.dispw.scene[])

	def autoscaleAction(self):
		self.dispw.view.fit_all()

	def orient1(self):
		self.dispw.reset_orient1()

	def orient2(self):
		self.dispw.reset_orient2()

	def resetAction(self):
		self.dispw.view.reset_orientation()
		self.dispw.view.autoscale()

	def screenshotAction(self):
		filters = "*.png;;*.bmp;;*.jpg;;*.*";
		defaultFilter = "*.png";

		path = QFileDialog.getSaveFileName(self, "Dump image", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]
		
		raw = self.dispw.view.rawarray()
		npixels = np.reshape(np.asarray(raw), (600,800,3))
		nnnpixels = np.flip(npixels, 0).reshape((800 * 600 * 3))

		rawiter = iter(nnnpixels)
		pixels = list(zip(rawiter, rawiter, rawiter))
		
		image = Image.new("RGB", (800, 600))
		image.putdata(pixels)

		image.save(path)

	def aboutAction(self):
		QMessageBox.about(self, self.tr("About ZenCad Shower"),
			self.tr("<h2>Shower</h2>"
			"<p>Author: mirmik(mirmikns@yandex.ru) 2018"
			"<p>Widget for display zencad geometry."));

	def keyPressEvent (self, event):
		if event.key() == Qt.Key_PageDown:
			self.dispw.pageDownKeyHandler()
		elif event.key() == Qt.Key_PageUp:
			self.dispw.pageUpKeyHandler()

class DisplayWidget(QWidget):
	def __init__(self, arg):
		QWidget.__init__(self)

		self.orient = 1

		self.inited = False
		self.painted = False

		self.scene = arg
		self.temporary1 = QPoint()	
		self.psi =   math.cos(math.pi / 4)
		self.phi = - math.cos(math.pi / 4)

		self.setBackgroundRole( QPalette.NoRole )
		self.setAttribute(Qt.WA_PaintOnScreen, True) 

	def reset_orient1(self):		
		self.orient = 1
		self.psi =   math.cos(math.pi / 4)
		self.phi = - math.cos(math.pi / 4)
		self.view.reset_orientation()
		self.view.autoscale()

	def reset_orient2(self):		
		self.orient = 2
		#self.view.reset_orientation()
		

	def set_orient1(self):
		self.view.set_projection(
			math.cos(self.psi) * math.cos(self.phi), 
			math.cos(self.psi) * math.sin(self.phi), 
			math.sin(self.psi)
		);

	def paintEvent(self, ev):
#		print("paintEvent")
		if self.inited and not self.painted:
			self.view.fit_all()
			self.view.must_be_resized()
			self.painted = True

	def showEvent(self, ev):
#		print("showEvent")
		self.viewer = zencad.Viewer(self.scene)
		self.view = self.viewer.create_view()
		self.view.set_window(self.winId())
		#self.view.set_gradient()
		
		self.set_orient1()
		self.view.set_triedron()
		self.viewer.set_triedron_axes()


		self.inited = True

	def resizeEvent(self, ev):
		if self.inited:
			self.view.must_be_resized()

	def paintEngine(self):
		return None

	def onLButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint;
		self.view.start_rotation(thePoint.x(), thePoint.y(), 1)

	def onRButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint;

	def onMButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint;

	def onMouseWheel(self, theFlags, theDelta, thePoint):
		aFactor = 16
	
		aX = thePoint.x()
		aY = thePoint.y()
	
		if (theDelta.y() > 0):
			aX += aFactor
			aY += aFactor
		else:
			aX -= aFactor
			aY -= aFactor
		
		self.view.zoom(thePoint.x(), thePoint.y(), aX, aY)

	def onMouseMove(self, theFlags, thePoint):
		mv = thePoint - self.temporary1
		self.temporary1 = thePoint

		if theFlags & Qt.LeftButton: 
			if self.orient == 1:  
				self.phi -= mv.x() * 0.01;
				self.psi += mv.y() * 0.01;
				self.set_orient1()
		
			if self.orient == 2:
					self.view.rotation(thePoint.x(), thePoint.y());
		
		if theFlags & Qt.RightButton:
			self.view.pan(mv.x(), -mv.y())
	
	def wheelEvent(self, e):
		self.onMouseWheel(e.buttons(), e.angleDelta(), e.pos());

	def mouseReleaseEvent(self, e):
		pass

	def mouseMoveEvent(self, e):
		self.onMouseMove(e.buttons(), e.pos());

	def mousePressEvent(self, e):
		if e.button() == Qt.LeftButton:
			self.onLButtonDown((e.buttons() | e.modifiers()), e.pos())
		
		elif e.button() == Qt.MidButton:
			self.onMButtonDown((e.buttons() | e.modifiers()), e.pos())
		
		elif e.button() == Qt.RightButton:
			self.onRButtonDown((e.buttons() | e.modifiers()), e.pos())

	def pageDownKeyHandler(self):
		x = self.width()/2
		y = self.height()/2
		factor = 16
		self.view.zoom(x, y, x - factor, y - factor)

	def pageUpKeyHandler(self):
		x = self.width()/2
		y = self.height()/2
		factor = 16
		self.view.zoom(x, y, x + factor, y + factor)

def show(scene):
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(os.path.dirname(__file__) + '/industrial-robot.svg'))

	fmt = QSurfaceFormat()
	fmt.setDepthBufferSize(24)
	fmt.setStencilBufferSize(8)
	fmt.setVersion(3, 2)
	fmt.setProfile(QSurfaceFormat.CoreProfile)
	QSurfaceFormat.setDefaultFormat(fmt)

	disp = DisplayWidget(scene)
	mw = MainWidget(disp);	

	mw.setCentralWidget(disp)

	mw.resize(800,600)

#	print("show")
	mw.show()

	app.exec_()