import zencad
import zencad.lazifier

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import math
import threading

class DisplayWidget(QWidget):
	intersectPointSignal = pyqtSignal(tuple)

	def __init__(self, arg, nointersect, showmarkers=True):
		QWidget.__init__(self)	
		self.setFocusPolicy(Qt.StrongFocus)
		self.orient = 1
		self.mousedown = False
		self.marker1=(zencad.pyservoce.point3(0,0,0),False)
		self.marker2=(zencad.pyservoce.point3(0,0,0),False)

		self.inited = False
		self.painted = False
		self.nointersect = nointersect
		self.showmarkers = showmarkers

		self.scene = arg
		self.temporary1 = QPoint()	
		self.started_yaw = 		math.pi * 2.8/4
		self.started_pitch = 	math.pi * -0.15
		self.yaw = self.started_yaw
		self.pitch = self.started_pitch
		self.last_redraw = time.time()

		self.setBackgroundRole( QPalette.NoRole )
		self.setAttribute(Qt.WA_PaintOnScreen, True) 
		self.setMouseTracking(True)

		self.animate_updated = threading.Event()

	def redraw(self):
		self.view.redraw()
		self.animate_updated.set()

	def reset_orient1(self):		
		self.orient = 1
		self.yaw = self.started_yaw
		self.pitch = self.started_pitch
		self.view.reset_orientation()
		self.view.autoscale()

	def reset_orient2(self):		
		self.orient = 2		

	def set_orient1(self):
		#self.view.set_orthogonal()
		self.view.set_direction(
			math.cos(self.pitch) * math.cos(self.yaw), 
			math.cos(self.pitch) * math.sin(self.yaw), 
			math.sin(self.pitch)
		);
		self.view.set_orthogonal()

	def update_orient1_from_view(self):
		"""Read actual camera orientation data from view"""
		x,y,z = self.view.direction()
		self.pitch = math.asin(z)
		x = x / math.cos(self.pitch)
		y = y / math.cos(self.pitch)
		self.yaw = math.atan2(y,x)

	def paintEvent(self, ev):
		if self.inited and not self.painted:
			self.view.fit_all(0.2)
			self.view.must_be_resized()
			self.painted = True

	def eye(self):
		return self.view.eye()

	def set_eye(self, pnt, orthogonal):
		self.view.set_eye(pnt)

		if orthogonal:
			self.view.set_orthogonal()

		self.update_orient1_from_view()

	def showEvent(self, ev):
		if self.inited != True:
		
			if self.showmarkers:
				zencad.lazifier.disable_lazy()
				self.msphere = zencad.sphere(1)
				self.MarkerQController = self.scene.add(self.msphere, zencad.Color(1,0,0))
				self.MarkerWController = self.scene.add(self.msphere, zencad.Color(0,1,0))
				zencad.lazifier.restore_lazy()

			self.viewer = zencad.Viewer(self.scene)
			self.view = self.viewer.create_view()
			self.view.set_window(self.winId())
			self.view.set_gradient()
			
			self.set_orient1()
			self.view.set_triedron()
			self.viewer.set_triedron_axes()
	
			if self.showmarkers:
				self.MarkerQController.hide(True)
				self.MarkerWController.hide(True)
	
			self.view.redraw()
			self.inited = True
		else:
			self.update()
			self.view.redraw()

	def resizeEvent(self, ev):
		if self.inited:
			self.view.must_be_resized()

	def paintEngine(self):
		return None

	def onLButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint;
		if self.orient == 2:
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
		#self.setFocus()
		mv = thePoint - self.temporary1
		self.temporary1 = thePoint

		self.lastPosition = thePoint

		modifiers = QApplication.keyboardModifiers()
		
		if modifiers == Qt.ShiftModifier:
			self.shift_pressed = True			
		else:
			self.shift_pressed = False


		if modifiers == Qt.AltModifier:
			if not self.alt_pressed:
				if self.orient == 2:
					self.view.start_rotation(thePoint.x(), thePoint.y(), 1)
			self.alt_pressed = True			
		else:
			self.alt_pressed = False
			
		if not self.nointersect and not self.mousedown:
			ip = self.view.intersect_point(thePoint.x(), thePoint.y())
			self.intersectPointSignal.emit(ip)

		if theFlags & Qt.LeftButton or self.alt_pressed: 
			if self.orient == 1:  
				self.yaw -= mv.x() * 0.01;
				self.pitch -= mv.y() * 0.01;
				if self.pitch > math.pi*0.4999: self.pitch = math.pi*0.4999
				if self.pitch < -math.pi*0.4999: self.pitch = -math.pi*0.4999
				self.set_orient1()
				self.view.redraw()
		
			if self.orient == 2:
					self.view.rotation(thePoint.x(), thePoint.y());
		
		if theFlags & Qt.RightButton or self.shift_pressed:
			self.view.pan(mv.x(), -mv.y())
	
	def wheelEvent(self, e):
		self.onMouseWheel(e.buttons(), e.angleDelta(), e.pos());

	def mouseReleaseEvent(self, e):
		pass

	def mouseMoveEvent(self, e):
		self.onMouseMove(e.buttons(), e.pos());

	def mouseReleaseEvent(self, e):
		self.mousedown = False

	def mousePressEvent(self, e):
		self.mousedown = True
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

	def markerQPressed(self):
		self.marker1 = self.view.intersect_point(self.lastPosition.x(), self.lastPosition.y())
		x = self.marker1[0].x
		y = self.marker1[0].y
		z = self.marker1[0].z
		
		if self.marker1[1]:
			self.mw.marker1Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
			print("Q: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(x,y,z))
		else:
			self.mw.marker1Label.setText(zencad.shower.QMARKER_MESSAGE)	
		self.mw.updateDistLabel()

		if self.showmarkers:
			zencad.lazifier.disable_lazy()
			self.MarkerQController.set_location(zencad.translate(x,y,z))
			zencad.lazifier.restore_lazy()
			self.MarkerQController.hide(not self.marker1[1])
			self.view.redraw()

	def markerWPressed(self):
		self.marker2 = self.view.intersect_point(self.lastPosition.x(), self.lastPosition.y())
		x = self.marker2[0].x
		y = self.marker2[0].y
		z = self.marker2[0].z

		if self.marker2[1]:
			self.mw.marker2Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
			print("W: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(x,y,z))
		else:
			self.mw.marker2Label.setText(zencad.shower.WMARKER_MESSAGE)	
		self.mw.updateDistLabel()
	
		if self.showmarkers:
			zencad.lazifier.disable_lazy()
			self.MarkerWController.set_location(zencad.translate(x,y,z))
			zencad.lazifier.restore_lazy()
			self.MarkerWController.hide(not self.marker2[1])
			self.view.redraw()

	def zoom_down(self):
		x = self.width()/2
		y = self.height()/2
		factor = 16
		self.view.zoom(x, y, x - factor, y - factor)

	def zoom_up(self):
		x = self.width()/2
		y = self.height()/2
		factor = 16
		self.view.zoom(x, y, x + factor, y + factor)

	
	def keyPressEvent(self, event):
		if self.mw.eventdebug:
			print("keyPressEvent", event.key())
			print(event.nativeVirtualKey())

		#print(event.key())
		#print(event.nativeVirtualKey())

		if event.key() == Qt.Key_Q:
			self.markerQPressed()
		if event.key() == Qt.Key_W:
			self.markerWPressed()
		if event.key() == Qt.Key_F3 or event.key() == Qt.Key_PageUp:
			self.zoom_up()
		if event.key() == Qt.Key_F4 or event.key() == Qt.Key_PageDown:
			self.zoom_down()
