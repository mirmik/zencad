# coding: utf-8

import zencad

import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

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
	
		#self.mScreen = QAction(self.tr("Screenshot..."), self)
		#self.mScreen.setStatusTip(self.tr("Do screen"))
		#connect(mScreen, SIGNAL(self.triggered()), self, SLOT(screenshot()))
	
		#self.mAboutAction = QAction(self.tr("About"), self)
		#self.mAboutAction.setStatusTip(self.tr("About the application"))
		#connect(mAboutAction, SIGNAL(self.triggered()), self, SLOT(about()))
	
		self.mAutoscale = QAction(self.tr("Autoscale"), self)
		self.mAutoscale.setStatusTip(self.tr("Autoscale"))
		self.mAutoscale.triggered.connect(self.autoscaleAction)
	
		#self.mOrient1 = QAction(self.tr("Orient1"), self)
		#self.mOrient1.setStatusTip(self.tr("Orient1"))
		#connect(mOrient1, SIGNAL(self.triggered()), self, SLOT(orient1()))
	
		#self.mOrient2 = QAction(self.tr("Orient2"), self)
		#self.mOrient2.setStatusTip(self.tr("Orient2"))
		#connect(mOrient2, SIGNAL(self.triggered()), self, SLOT(orient2()))

	def createMenus(self):
		self.mFileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.mFileMenu.addAction(self.mStlExport)
		#self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)
	
		self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
		self.mNavigationMenu.addAction(self.mAutoscale)
		#self.mNavigationMenu.addAction(self.mOrient1)
		#self.mNavigationMenu.addAction(self.mOrient2)
	
		#self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		#self.mHelpMenu.addAction(self.mAboutAction)
		
	def createToolbars(self):
		pass

	def exportStlAction(self):
		pass

	def autoscaleAction(self):
		self.dispw.view.fit_all()

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

	def set_orient1(self):
		self.view.set_projection(
			math.cos(self.psi) * math.cos(self.phi), 
			math.cos(self.psi) * math.sin(self.phi), 
			math.sin(self.psi)
		);

	def paintEvent(self, ev):
		if self.inited and not self.painted:
			self.view.fit_all()
			self.view.must_be_resized()
			self.painted = True

	def showEvent(self, ev):
		self.viewer = zencad.Viewer(self.scene)
		self.view = self.viewer.create_view()
		
		self.set_orient1()
		self.view.set_triedron()
		self.viewer.set_triedron_axes()

		self.view.set_gradient()

		self.view.set_window(self.winId())

		self.inited = True

	def resizeEvent(self, ev):
		if self.inited:
			self.view.must_be_resized()

	def paintEngine(self):
		return None

	def onLButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint;

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
				pass
				#if (theFlags & Qt::LeftButton:
				#	m_view->Rotation(thePoint.x(), thePoint.y());
				#	double Vx;
				#	double Vy;
				#	double Vz;
				#	m_view.set_projection(Vx, Vy, Vz);
		
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

def show(scene):
	app = QApplication(sys.argv)

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
	mw.show()

	app.exec_()