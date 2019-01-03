# coding: utf-8

import zencad
import zencad.lazy
import pyservoce

import sys
import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PIL import Image
import numpy as np

import time
import threading
import signal

#from OpenGL.GL import *
#from OpenGL.GLUT import *
#from OpenGL.GLU import *

import math

ensave = None
desave = None
onplace = None

def disable_lazy():
	global ensave, desave, onplace
	ensave = zencad.lazy.encache 
	desave = zencad.lazy.decache
	onplace = zencad.lazy.onplace
	zencad.lazy.encache = False
	zencad.lazy.decache = False
	zencad.lazy.onplace = True

def restore_lazy():
	zencad.lazy.onplace = onplace
	zencad.lazy.encache = ensave
	zencad.lazy.decache = desave

class MainWidget(QMainWindow):
	def __init__(self, dispw):
		QMainWindow.__init__(self)
		self.cw = QWidget()
		self.dispw = dispw
		self.layout = QVBoxLayout()
		self.infolay = QHBoxLayout()

		self.setWindowTitle("zenwidget");
		#self.setWindowIcon(QIcon(":/industrial-robot.svg"));

		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0,0,0,0)

		self.poslbl = QLabel("PosLbl")
		self.poslbl.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.poslbl.setAlignment(Qt.AlignCenter)

		self.marker1=(zencad.pyservoce.point3(0,0,0),False)
		self.marker2=(zencad.pyservoce.point3(0,0,0),False)

		self.marker1Label = QLabel("MarkerQ")
		self.marker1Label.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.marker1Label.setStyleSheet("QLabel { background-color : rgb(100,0,0); color : white; }");
		self.marker1Label.setAlignment(Qt.AlignCenter)

		self.marker2Label = QLabel("MarkerW")
		self.marker2Label.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.marker2Label.setStyleSheet("QLabel { background-color : rgb(0,100,0); color : white; }");
		self.marker2Label.setAlignment(Qt.AlignCenter)

		self.markerDistLabel = QLabel("Dist")
		self.markerDistLabel.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);
		self.markerDistLabel.setAlignment(Qt.AlignCenter)

		self.infolay.addWidget(self.poslbl)
		self.infolay.addWidget(self.marker1Label)
		self.infolay.addWidget(self.marker2Label)
		self.infolay.addWidget(self.markerDistLabel)

		self.layout.addWidget(self.dispw)
		self.layout.addLayout(self.infolay)
		self.cw.setLayout(self.layout)

		self.setCentralWidget(self.cw)

		self.createActions();
		self.createMenus();
		self.createToolbars();

		self.dispw.intersectPointSignal.connect(self.poslblSlot)

	def poslblSlot(self, obj):
		#print(obj)
		if obj[1]:
			self.poslbl.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(obj[0].x, obj[0].y, obj[0].z))
		else:
			self.poslbl.setText("")
			self.update()

	def createActions(self):
		self.mExitAction = QAction(self.tr("Exit"), self)
		self.mExitAction.setShortcut(self.tr("Ctrl+Q"))
		self.mExitAction.setStatusTip(self.tr("Exit the application"))
		self.mExitAction.triggered.connect(self.close)
	
		self.mStlExport = QAction(self.tr("Export STL..."), self)
		self.mStlExport.setStatusTip(self.tr("Export file with external STL-Mesh format"))
		self.mStlExport.triggered.connect(self.exportStlAction);

		self.mBrepExport = QAction(self.tr("Export BREP..."), self)
		self.mBrepExport.setStatusTip(self.tr("Export file in BREP format"))
		self.mBrepExport.triggered.connect(self.exportBrepAction);
	
		self.mScreen = QAction(self.tr("Screenshot..."), self)
		self.mScreen.setStatusTip(self.tr("Do screen"))
		self.mScreen.triggered.connect(self.screenshotAction)
	
		self.mAboutAction = QAction(self.tr("About"), self)
		self.mAboutAction.setStatusTip(self.tr("About the application"))
		self.mAboutAction.triggered.connect(self.aboutAction)
	
		self.mReset = QAction(self.tr("Reset"), self)
		self.mReset.setStatusTip(self.tr("Reset"))
		self.mReset.triggered.connect(self.resetAction)

		self.mCentering = QAction(self.tr("Centering"), self)
		self.mCentering.setStatusTip(self.tr("Centering"))
		self.mCentering.triggered.connect(self.centeringAction)

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
		self.mFileMenu.addAction(self.mBrepExport)
		self.mFileMenu.addAction(self.mScreen)
		self.mFileMenu.addSeparator()
		self.mFileMenu.addAction(self.mExitAction)
	
		self.mNavigationMenu = self.menuBar().addMenu(self.tr("&Navigation"))
		self.mNavigationMenu.addAction(self.mReset)
		self.mNavigationMenu.addAction(self.mCentering)
		self.mNavigationMenu.addAction(self.mAutoscale)
		self.mNavigationMenu.addAction(self.mOrient1)
		self.mNavigationMenu.addAction(self.mOrient2)
	
		self.mHelpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.mHelpMenu.addAction(self.mAboutAction)
		
	def createToolbars(self):
		#self.btoolbar = QToolBar()
		#self.lbl = QLabel("HelloWorld")
		#self.btoolbar.addWidget(self.lbl)
		#self.addToolBar(Qt.BottomToolBarArea, self.btoolbar)
		pass

	def exportStlAction(self):
		d, okPressed = QInputDialog.getDouble(self, "Get double","Value:", 0.01, 0, 10, 10)
		if not okPressed:
			return

		filters = "*.stl;;*.*";
		defaultFilter = "*.stl";

		path = QFileDialog.getSaveFileName(self, "STL Export", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]

		pyservoce.make_stl(self.dispw.scene[0].shape(), path, d)

	def exportBrepAction(self):
		filters = "*.brep;;*.*";
		defaultFilter = "*.brep";

		path = QFileDialog.getSaveFileName(self, "BREP Export", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]

		pyservoce.brep_write(self.dispw.scene[0].shape(), path)

	def autoscaleAction(self):
		self.dispw.view.fit_all()

	def centeringAction(self):
		self.dispw.view.centering()

	def orient1(self):
		self.dispw.reset_orient1()

	def orient2(self):
		self.dispw.reset_orient2()

	def resetAction(self):
		self.dispw.view.reset_orientation()
		self.dispw.view.autoscale()

	def updateDistLabel(self):
		qx,qy,qz = self.marker1[0].x, self.marker1[0].y, self.marker1[0].z
		wx,wy,wz = self.marker2[0].x, self.marker2[0].y, self.marker2[0].z
		xx,yy,zz = wx-qx, wy-qy, wz-qz
		dist = math.sqrt(xx**2 + yy**2 + zz**2)
		self.markerDistLabel.setText("{}".format(dist))		

	def screenshotAction(self):
		filters = "*.png;;*.bmp;;*.jpg;;*.*";
		defaultFilter = "*.png";

		path = QFileDialog.getSaveFileName(self, "Dump image", 
			QDir.currentPath(),
			filters, defaultFilter);

		path = path[0]
		
		w = self.dispw.width()
		h = self.dispw.height()

		raw = self.dispw.view.rawarray(w,h)
		npixels = np.reshape(np.asarray(raw), (h,w,3))
		nnnpixels = np.flip(npixels, 0).reshape((w * h * 3))

		rawiter = iter(nnnpixels)
		pixels = list(zip(rawiter, rawiter, rawiter))
		
		image = Image.new("RGB", (w, h))
		image.putdata(pixels)

		image.save(path)

	def aboutAction(self):
		QMessageBox.about(self, self.tr("About ZenCad Shower"),
			self.tr("<h2>Shower</h2>"
			"<p>Author: mirmik(mirmikns@yandex.ru) 2018"
			"<p>Widget for display zencad geometry."));

	def keyPressEvent (self, event):
		if event.key() == Qt.Key_Q:
			self.marker1 = self.dispw.view.intersect_point(self.dispw.lastPosition.x(), self.dispw.lastPosition.y())
			x = self.marker1[0].x
			y = self.marker1[0].y
			z = self.marker1[0].z
			self.marker1Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
			self.updateDistLabel()

			if self.dispw.showmarkers:
				disable_lazy()
				self.dispw.MarkerQController.set_location(zencad.translate(x,y,z))
				restore_lazy()
				self.dispw.MarkerQController.hide(not self.marker1[1])
				self.dispw.view.redraw()
		
		if event.key() == Qt.Key_W:
			self.marker2 = self.dispw.view.intersect_point(self.dispw.lastPosition.x(), self.dispw.lastPosition.y())
			x = self.marker2[0].x
			y = self.marker2[0].y
			z = self.marker2[0].z
			self.marker2Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
			self.updateDistLabel()
		
			if self.dispw.showmarkers:
				disable_lazy()
				self.dispw.MarkerWController.set_location(zencad.translate(x,y,z))
				restore_lazy()
				self.dispw.MarkerWController.hide(not self.marker2[1])
				self.dispw.view.redraw()
		
		if event.key() == Qt.Key_PageDown:
			self.dispw.pageDownKeyHandler()
		elif event.key() == Qt.Key_PageUp:
			self.dispw.pageUpKeyHandler()

class DisplayWidget(QWidget):
	intersectPointSignal = pyqtSignal(tuple)

	def __init__(self, arg, nointersect, showmarkers):
		QWidget.__init__(self)
	
		self.orient = 1

		self.inited = False
		self.painted = False
		self.nointersect = nointersect
		self.showmarkers = showmarkers

		self.scene = arg
		self.temporary1 = QPoint()	
		self.psi =   math.cos(math.pi / 4)
		self.phi = - math.cos(math.pi / 4)

		self.setBackgroundRole( QPalette.NoRole )
		self.setAttribute(Qt.WA_PaintOnScreen, True) 
		self.setMouseTracking(True)

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
		if self.showmarkers:
			self.msphere = zencad.sphere(1)
			self.MarkerQController = self.scene.add(self.msphere.unlazy(), zencad.Color(1,0,0))
			self.MarkerWController = self.scene.add(self.msphere.unlazy(), zencad.Color(0,1,0))

		self.viewer = zencad.Viewer(self.scene)
		self.view = self.viewer.create_view()
		self.view.set_window(self.winId())
		#self.view.set_gradient()
		
		self.set_orient1()
		self.view.set_triedron()
		self.viewer.set_triedron_axes()

		if self.showmarkers:
			self.MarkerQController.hide(True)
			self.MarkerWController.hide(True)

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

		self.lastPosition = thePoint

		if not self.nointersect:
			ip = self.view.intersect_point(thePoint.x(), thePoint.y())
			self.intersectPointSignal.emit(ip)

		if theFlags & Qt.LeftButton: 
			if self.orient == 1:  
				self.phi -= mv.x() * 0.01;
				self.psi += mv.y() * 0.01;
				if self.psi > math.pi*0.4999: self.psi = math.pi*0.4999
				if self.psi < -math.pi*0.4999: self.psi = -math.pi*0.4999
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

class update_loop(QThread):
	def __init__(self, parent, updater_function, wdg, update_time):
		QThread.__init__(self, parent)
		self.updater_function = updater_function 
		self.wdg = wdg
		self.update_time = update_time

	def run(self):
		while 1:
			ensave = zencad.lazy.encache 
			desave = zencad.lazy.decache
			onplace = zencad.lazy.onplace
			if self.wdg.inited:
				zencad.lazy.encache = False
				zencad.lazy.decache = False
				zencad.lazy.onplace = True
				self.updater_function(self.wdg.viewer)
				zencad.lazy.onplace = onplace
				zencad.lazy.encache = ensave
				zencad.lazy.decache = desave
				#time.sleep(50/1000)
		

def show(scene, animate = None, update_time = 50, nointersect=False, showmarkers=True):
	app = QApplication(sys.argv)
	#app.lastWindowClosed.connect(app.quit)
	app.lastWindowClosed.connect(sys.exit)

	app.setWindowIcon(QIcon(os.path.dirname(__file__) + '/industrial-robot.svg'))

	fmt = QSurfaceFormat()
	fmt.setDepthBufferSize(24)
	fmt.setStencilBufferSize(8)
	fmt.setVersion(3, 2)
	fmt.setProfile(QSurfaceFormat.CoreProfile)
	QSurfaceFormat.setDefaultFormat(fmt)

	disp = DisplayWidget(scene, nointersect, showmarkers)
	mw = MainWidget(disp);	
	mw.resize(800,600)

	if animate != None:
		thr = update_loop(mw, animate, disp, update_time)
		thr.start()
		#thr = QThread(update_loop, animate, disp, update_time)
		#thr.start()

#	def sigint_handler(*args):
#		"""Handler for the SIGINT signal."""
#		sys.stderr.write('\r')
#		if QMessageBox.question(None, '', "Are you sure you want to quit?",
#								QMessageBox.Yes | QMessageBox.No,
#								QMessageBox.No) == QMessageBox.Yes:
#			QApplication.quit()
#	
#	signal.signal(signal.SIGINT, sigint_handler)

#	print("show")
	mw.show()

	return app.exec()