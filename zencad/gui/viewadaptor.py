import zencad
import zencad.lazifier

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *

from OpenGL.GLUT import *
from OpenGL.GL import *
from OpenGL.GLU import *

import os
import time
import math
import threading

import pyservoce
import zencad.configure

from zencad.util import print_to_stderr

#__TRACE__ = False
#OPTION_RETRANSLATE_KEYS_TO_MAINCOMMUNICATOR = True

def trace(*argv):
	if zencad.configure.CONFIGURE_VIEWADAPTOR_TRACE:
		print_to_stderr("DISPTRACE:", *argv)

class DisplayWidget(QGLWidget):
	tracking_info_signal = pyqtSignal(tuple)
	markerRequestQ = pyqtSignal(tuple)
	markerRequestW = pyqtSignal(tuple)

	locationChanged = pyqtSignal(dict)
	signal_key_pressed = pyqtSignal(str)
	signal_key_pressed_raw = pyqtSignal(int, int)
	signal_key_released_raw = pyqtSignal(int, int)
	signal_screenshot_reply = pyqtSignal(bytes, tuple)

	zoom_koeff_key = 1.3
	zoom_koeff_mouse = 1.1

	def __init__(self, scene, need_prescale=True, view=None, showmarkers=True):
		trace("construct DisplayWidget")
		QWidget.__init__(self)
		self.setFocusPolicy(Qt.StrongFocus)
		self.orient = 1
		self.mousedown = False
		self.marker1 = (zencad.pyservoce.point3(0, 0, 0), False)
		self.marker2 = (zencad.pyservoce.point3(0, 0, 0), False)

		self.need_prescale = need_prescale
		self.inited = False
		self.painted = False
		self.tracking_mode = False
		#self.nointersect = nointersect
		self.showmarkers = showmarkers

		self.scene = scene
		self.scene.viewer.set_triedron_axes(True)
		self.view = view
 
		self.temporary1 = QPoint()
		self.started_yaw = math.pi * (7 / 16)
		self.started_pitch = math.pi * -0.15
		self.yaw = self.started_yaw
		self.pitch = self.started_pitch
		self.last_redraw = time.time()

		self.setBackgroundRole(QPalette.NoRole)
		self.setAttribute(Qt.WA_PaintOnScreen, True)
		self.setMouseTracking(True)

		self.animate_updated = threading.Event()
		self.count_of_helped_shapes = 0

		self.alt_pressed = False
		self.shift_pressed = False

	def redraw(self):
		self.animate_updated.clear()
		self.view.redraw()
		self.last_redraw = time.time()
		self.animate_updated.set()

	def continuous_redraw(self):
		"""Этот слот использует поток анимации для обновления
		виджета"""

		if time.time() - self.last_redraw > 0.01:
			self.redraw()
		else:
			self.animate_updated.set()

	def reset_orient1(self):
		self.orient = 1
		self.yaw = self.started_yaw
		self.pitch = self.started_pitch
		self.set_orient1()
		self.update_orient1_from_view()
		self.view.redraw()

	def reset_orient2(self):
		self.orient = 2

	def autoscale(self):
		self.view.fit_all(0.2)

	def reset_orient(self):
		self.reset_orient1()
		self.autoscale()
		self.view.redraw()

	def set_orient1(self):
		# self.view.set_orthogonal()
		self.view.set_direction(
			math.cos(self.pitch) * math.cos(self.yaw),
			math.cos(self.pitch) * math.sin(self.yaw),
			math.sin(self.pitch),
		)
		self.view.set_orthogonal()

	def update_orient1_from_view(self):
		"""Read actual camera orientation data from view"""
		x, y, z = self.view.direction()
		self.pitch = math.asin(z)
		x = x / math.cos(self.pitch)
		y = y / math.cos(self.pitch)
		self.yaw = math.atan2(y, x)

	def eye(self):
		return self.view.eye()

	def set_eye(self, pnt, orthogonal):
		self.view.set_eye(pnt)

		if orthogonal:
			self.view.set_orthogonal()

		self.update_orient1_from_view()

	def create_qwmarkers(self):
		if self.showmarkers:
			zencad.lazifier.disable_lazy()
			self.msphere = zencad.sphere(1)
			self.MarkerQController = self.scene.add(
				self.msphere, zencad.Color(1, 0, 0)
			)
			self.MarkerWController = self.scene.add(
				self.msphere, zencad.Color(0, 1, 0)
			)
			zencad.lazifier.restore_lazy()

			self.MarkerQController.hide(True)
			self.MarkerWController.hide(True)

			self.count_of_helped_shapes += 2

	def showEvent(self, ev):
		trace("DisplayWidget::showEvent")
		if self.inited != True:
			trace("DisplayWidget::showEvent: init")

			self.viewer = self.scene.viewer
	
			if self.view is None:
				self.view = self.viewer.create_view()

			self.set_orient1()
			self.view.set_window(self.winId())
			
			self.create_qwmarkers()

			#self.view.redraw()
			self.inited = True
		else:
			pass
			#self.update()
			#self.view.redraw()

		#self.location_changed_handle()
		trace("DisplayWidget::showEvent: finish")

	def paintEvent(self, ev):
		trace("DisplayWidget::paintEvent")
		if self.inited and not self.painted:
			if self.need_prescale:
				self.prescale()
			self.view.must_be_resized()
			self.painted = True
		trace("DisplayWidget::paintEvent: finish")

	def prescale(self):
		self.reset_orient1()
		self.view.fit_all(0.2)
		self.location_changed_handle()

	def resizeEvent(self, ev):
		if self.inited:
			self.view.must_be_resized()

	def resize_addon(self):
		if self.inited:
			self.view.must_be_resized()

	def paintEngine(self):
		return None

	def onLButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint
		if self.orient == 2:
			self.view.start_rotation(thePoint.x(), thePoint.y(), 1)

	def onRButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint

	def onMButtonDown(self, theFlags, thePoint):
		self.temporary1 = thePoint

	def onMouseWheel(self, theFlags, theDelta, thePoint):
		#aFactor = 16

		#aX = thePoint.x()
		#aY = thePoint.y()

		if theDelta.y() > 0:
			self.zoom_up(self.zoom_koeff_mouse)
		#	aX += aFactor
		#	aY += aFactor
		else:
			self.zoom_down(self.zoom_koeff_mouse)
		#	aX -= aFactor
		#	aY -= aFactor

		#self.view.zoom(thePoint.x(), thePoint.y(), aX, aY)

	def onMouseMove(self, theFlags, thePoint):
		# self.setFocus()
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

		if self.tracking_mode and not self.mousedown:
			ip = self.view.intersect_point(thePoint.x(), thePoint.y())
			self.tracking_info_signal.emit(ip)

		if theFlags & Qt.LeftButton or self.alt_pressed:
			if self.orient == 1:
				self.yaw -= mv.x() * 0.01
				self.pitch -= mv.y() * 0.01
				if self.pitch > math.pi * 0.4999:
					self.pitch = math.pi * 0.4999
				if self.pitch < -math.pi * 0.4999:
					self.pitch = -math.pi * 0.4999
				self.set_orient1()
				self.location_changed_handle()
				self.view.redraw()

			if self.orient == 2:
				self.view.rotation(thePoint.x(), thePoint.y())
			self.location_changed_handle()

		if theFlags & Qt.RightButton or self.shift_pressed:
			self.view.pan(mv.x(), -mv.y())
			self.location_changed_handle()

	def wheelEvent(self, e):
		self.onMouseWheel(e.buttons(), e.angleDelta(), e.pos())

	def mouseReleaseEvent(self, e):
		pass

	def mouseMoveEvent(self, e):
		self.onMouseMove(e.buttons(), e.pos())

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

	def markerQPressed(self):
		self.marker1 = self.view.intersect_point(
			self.lastPosition.x(), self.lastPosition.y()
		)
		x = self.marker1[0].x
		y = self.marker1[0].y
		z = self.marker1[0].z

		self.markerRequestQ.emit((x,y,z))
		self.redraw_marker("q",x,y,z)

		#if self.marker1[1]:
		#	self.mw.marker1Label.setText(
		#		"x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x, y, z)
		#	)
		#	print(
		#		"Q: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(
		#			x, y, z
		#		)
		#	)
		#else:
		#	self.mw.marker1Label.setText(zencad.shower.QMARKER_MESSAGE)
		#self.mw.updateDistLabel()

		#if self.showmarkers:
		#	zencad.lazifier.disable_lazy()
		#	self.MarkerQController.set_location(zencad.translate(x, y, z))
		#	zencad.lazifier.restore_lazy()
		#	self.MarkerQController.hide(not self.marker1[1])
		#	self.view.redraw()

	def markerWPressed(self):
		self.marker2 = self.view.intersect_point(
			self.lastPosition.x(), self.lastPosition.y()
		)
		x = self.marker2[0].x
		y = self.marker2[0].y
		z = self.marker2[0].z

		self.markerRequestW.emit((x,y,z))
		self.redraw_marker("w",x,y,z)

		#if self.marker2[1]:
		#	self.mw.marker2Label.setText(
		#		"x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x, y, z)
		#	)
		#	print(
		#		"W: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(
		#			x, y, z
		#		)
		#	)
		#else:
		#	self.mw.marker2Label.setText(zencad.shower.WMARKER_MESSAGE)
		#self.mw.updateDistLabel()

		#if self.showmarkers:
		#	zencad.lazifier.disable_lazy()
		#	self.MarkerWController.set_location(zencad.translate(x, y, z))
		#	zencad.lazifier.restore_lazy()
		#	self.MarkerWController.hide(not self.marker2[1])
		#	self.view.redraw()

	def location_changed_handle(self):
		#pass
		self.locationChanged.emit(self.location())

	def redraw_marker(self, qw, x, y, z):
		if qw == "q":
			marker = self.MarkerQController
		elif qw == "w":
			marker = self.MarkerWController

		marker.set_location(zencad.translate(x, y, z))
		marker.hide(x == 0 and y == 0 and z == 0)

		self.redraw()

	def zoom_down(self, koeff):
		self.view.set_scale(self.view.scale()*(1/koeff))
		self.location_changed_handle()

	def zoom_up(self, koeff):
		self.view.set_scale(self.view.scale()*koeff)
		self.location_changed_handle()

	def keyPressEvent(self, event):
		trace("keyPressEvent", event.key())
		trace(event.nativeVirtualKey())

		modifiers = QApplication.keyboardModifiers()

		if event.key() == Qt.Key_Q:
			self.markerQPressed()
		elif event.key() == Qt.Key_W:
			self.markerWPressed()
		elif event.key() == Qt.Key_F3 or event.key() == Qt.Key_PageUp:
			self.zoom_up(self.zoom_koeff_key)
		elif event.key() == Qt.Key_F4 or event.key() == Qt.Key_PageDown:
			self.zoom_down(self.zoom_koeff_key)

		#elif event.key() == Qt.Key_F11:
		#	self.signal_key_pressed.emit("F11")

		#elif event.key() == Qt.Key_F10:
		#	self.signal_key_pressed.emit("F10")

		else:
			# If signal not handling here, translate it onto top level
			if zencad.configure.CONFIGURE_VIEWADAPTOR_RETRANSLATE_KEYS:
				self.signal_key_pressed_raw.emit(event.key(), modifiers)

			#self.setWindowState(Qt.WindowFullScreen)

	def keyReleaseEvent(self, event):
		modifiers = QApplication.keyboardModifiers()
		
		if zencad.configure.CONFIGURE_VIEWADAPTOR_RETRANSLATE_KEYS:
			self.signal_key_released_raw.emit(event.key(), modifiers)

	def external_communication_command(self, data):
		cmd = data["cmd"]

		trace("external_command:", data)

		if cmd == "autoscale": self.autoscale()
		elif cmd == "resetview": self.reset_orient()
		elif cmd == "redraw": self.redraw()
		elif cmd == "resize": self.resize_addon()
		elif cmd == "orient1": self.reset_orient1()
		elif cmd == "orient2": self.reset_orient2()
		elif cmd == "centering": self.view.centering() # TODO: Неправильно работает
		elif cmd == "location": self.set_location(data["dct"])
		elif cmd == "exportstl": self.addon_exportstl()
		elif cmd == "exportbrep": self.addon_exportbrep()
		elif cmd == "to_freecad": self.addon_to_freecad_action()
		elif cmd == "tracking": self.tracking_mode = data["en"]
		elif cmd == "screenshot": self.addon_screenshot_upload()
		elif cmd == "console": sys.stdout.write(data["data"])
			
		else:
			print("UNRECOGNIZED_COMMUNICATION_COMMAND:", cmd)

	widget_closed = pyqtSignal()
	def closeEvent(self, ev):
		self.widget_closed.emit()

	def set_location(self, dct):
		scale = dct["scale"]
		eye = dct["eye"]
		center = dct["center"]

		self.view.set_center(center)
		self.view.set_eye(eye)
		self.view.set_scale(scale)
		self.view.redraw()

		self.update_orient1_from_view()
		self.location_changed_handle()

	def location(self):
		return {
			"scale": self.view.scale(),
			"eye": self.view.eye(),
			"center": self.view.center()
		}

	def raw_screen_dump(self):
		return glReadPixels(0, 0, self.width(), self.height(), GL_RGBA, GL_UNSIGNED_BYTE)

	def screen(self):
		QPixmap.fromImage(
			QImage(self.raw_screen_dump, self.width(), self.height(), 
				QImage.Format.Format_RGBA8888).mirrored(False,True))

	def addon_screenshot_upload(self):
		buf = glReadPixels(0, 0, self.width(), self.height(), GL_RGBA, GL_UNSIGNED_BYTE)

		arr, size = buf, (self.size().width(), self.height())
		self.signal_screenshot_reply.emit(arr, size)

	def export_file_for_one_shape(self, filters, defaultFilter):
		if self.scene.total() != 1 + self.count_of_helped_shapes: 
			print("more/less than one shape in scene:", self.scene.total() - self.count_of_helped_shapes)
			return False, "", None

		shape = self.scene[0].shape()

		path = QFileDialog.getSaveFileName(
			self, "STL Export", QDir.currentPath(), filters, defaultFilter
		)

		path = path[0]
		return True, path, shape

	def addon_exportstl(self):
		ok, path, shape = self.export_file_for_one_shape(
			filters = "*.stl;;*.*",
			defaultFilter = "*.stl")

		if ok == False or path == "":
			return

		d, okPressed = QInputDialog.getDouble(
			self, "Get double", "Value:", 0.01, 0, 10, 10
		)
		
		if not okPressed:
			return

		pyservoce.make_stl(shape, path, d)
		print("Make STL procedure finished.")

	def addon_exportbrep(self):
		ok, path, shape = self.export_file_for_one_shape(
			filters = "*.brep;;*.*",
			defaultFilter = "*.brep")

		if ok == False or path == "":
			return
		
		pyservoce.brep_write(shape, path)
		print("Save BREP procedure finished.")

	def addon_to_freecad_action(self):
		import tempfile

		if self.scene.total() != 1 + self.count_of_helped_shapes: 
			print("more/less than one shape in scene:", self.scene.total() - self.count_of_helped_shapes)
			return False, "", None

		tmpfl = tempfile.mktemp(".brep")
		#print(tmpfl)
		cb = QApplication.clipboard()
		cb.clear(mode=cb.Clipboard)
		cb.setText(
			'import Part; export = Part.Shape(); export.read("{}"); Part.show(export); Gui.activeDocument().activeView().viewAxonometric(); Gui.SendMsgToActiveView("ViewFit")'.format(
				tmpfl
			),
			mode=cb.Clipboard,
		)
		pyservoce.brep_write(self.scene[0].shape(), tmpfl)
		QMessageBox.information(
			self, self.tr("ToFreeCad"), self.tr("Script copied to clipboard. Don't close gui before script placing.")
		)



def standalone(*args, **kwargs):
	"""Запуск отдельного виджета для теста функциональности.
	"""

	zencad.gui.application.common_unbouded_proc(
		*args, need_prescale=True, **kwargs)
	#app = QApplication([])
	#zencad.opengl.init_opengl()

	#wdg = DisplayWidget(scene)    
	#wdg.show()

	#app.exec()

def screenshot_return_send_dec(communicator):
	def screenshot_return_send(arg, size):
		#communicator.send({"cmd":"tobuffer", "data": (arg, size) })
		communicator.send({"cmd":"finish_screen", "data": (arg, size)})
	return screenshot_return_send

def bind_widget_signal(widget, communicator):
	widget.markerRequestQ.connect(lambda arg:communicator.send({
		"cmd":"qmarker", "x": arg[0], "y": arg[1], "z": arg[2] }))
	widget.markerRequestW.connect(lambda arg:communicator.send({
		"cmd":"wmarker", "x": arg[0], "y": arg[1], "z": arg[2] }))
	widget.locationChanged.connect(lambda arg:communicator.send({
		"cmd":"location", "loc": arg }))
	widget.signal_key_pressed.connect(lambda arg:communicator.send({
		"cmd":"keypressed", "key": arg }))
	widget.signal_key_pressed_raw.connect(lambda key, modifiers:communicator.send({
		"cmd":"keypressed_raw", "key": key, "modifiers": modifiers }))
	widget.signal_key_released_raw.connect(lambda key, modifiers:communicator.send({
		"cmd":"keyreleased_raw", "key": key, "modifiers": modifiers }))
	widget.tracking_info_signal.connect(lambda arg:communicator.send({
		"cmd":"trackinfo", "data": arg }))
	widget.signal_screenshot_reply.connect(screenshot_return_send_dec(communicator))


def brep_hot_open(path):
	import zencad.convert
	scn = zencad.Scene()

	scn.add(zencad.convert.from_brep(path).unlazy())

	zencad.gui.application.common_unbouded_proc(scene = scn, need_prescale=True)