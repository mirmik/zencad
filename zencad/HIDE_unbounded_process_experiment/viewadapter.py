#!/usr/bin/env python3

import pyservoce
import math

from zencad.lazifier import disable_lazy, restore_lazy  # for markers

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class GeometryWidget(QWidget):
    orient_mode_changed_signal = pyqtSignal(int)
    showready_signal = pyqtSignal()

    def __init__(self, scene, connect=None):
        QWidget.__init__(self)
        self.scene = scene
        self.inited = False
        self.viewer_inited = False
        self.painted = False
        self.orient_mode = 1
        self.mousedown = False

        self.temporary1 = QPoint()
        self.psi = math.cos(math.pi / 4)
        self.phi = -math.cos(math.pi / 4)

        self.setMouseTracking(True)
        self.setBackgroundRole(QPalette.NoRole)
        self.setAttribute(Qt.WA_PaintOnScreen, True)

    def get_wid(self):
        return int(self.winId())

    def set_orient1(self):
        self.view.set_projection(
            math.cos(self.psi) * math.cos(self.phi),
            math.cos(self.psi) * math.sin(self.phi),
            math.sin(self.psi),
        )
        self.view.redraw()

    def update_orient1_from_view(self):
        x, y, z = self.view.proj()
        self.psi = math.asin(z)
        x = x / math.cos(self.psi)
        y = y / math.cos(self.psi)
        self.phi = math.atan2(y, x)

    def set_orient_mode(self, num):
        if num == self.orient_mode:
            return

        self.orient_mode = num
        if num == 1:
            self.update_orient1_from_view()
            self.set_axonometric_projection()
        elif num == 2:
            pass
        else:
            raise Exception("unregistred orient mode")

        pass

    def action_reset(self):
        self.psi = math.cos(math.pi / 4)
        self.phi = -math.cos(math.pi / 4)
        self.orient_mode = 1
        self.view.set_orthogonal()
        self.set_orient1()
        self.action_autoscale()
        self.view.redraw()

    def action_autoscale(self):
        self.view.fit_all()

    def action_centering(self):
        self.view.centering()
        self.set_orient1()

    def set_axonometric_projection(self):
        self.view.set_orthogonal()

    def stop(self):
        self.setHidden(True)
        self.ctransler.stop()
        self.viewer.close()

    def init_viewer(self):
        self.viewer = pyservoce.Viewer(self.scene)
        self.view = self.viewer.create_view()
        self.viewer.set_triedron_axes()
        self.viewer_inited = True

    def showEvent(self, ev):
        if self.inited != True:
            # if self.showmarkers:
            # 	disable_lazy()
            # 	self.msphere = zencad.sphere(1)
            # 	self.MarkerQController = self.scene.add(self.msphere, zencad.Color(1,0,0))
            # 	self.MarkerWController = self.scene.add(self.msphere, zencad.Color(0,1,0))
            # 	restore_lazy()
            if self.viewer_inited == False:
                self.init_viewer()

            self.view.set_window(self.winId())
            self.view.set_gradient()

            # self.set_orient1()
            self.view.fit_all()
            self.view.set_triedron()

            # if self.showmarkers:
            # 	self.MarkerQController.hide(True)
            # 	self.MarkerWController.hide(True)

            # self.view.must_be_resized()
            self.view.redraw()
            self.showready_signal.emit()
            self.inited = True
        else:
            pass
            self.view.redraw()

    def paintEvent(self, ev):
        if self.inited and not self.painted:
            self.view.fit_all()
            self.view.must_be_resized()
            self.painted = True
        self.view.redraw()

    def resizeEvent(self, ev):
        if self.inited:
            self.view.must_be_resized()

    def paintEngine(self):
        return None

    def onLButtonDown(self, theFlags, thePoint):
        self.temporary1 = thePoint
        self.view.start_rotation(thePoint.x(), thePoint.y(), 1)

    def onRButtonDown(self, theFlags, thePoint):
        self.temporary1 = thePoint

    def onMButtonDown(self, theFlags, thePoint):
        self.temporary1 = thePoint

    def onMouseWheel(self, theFlags, theDelta, thePoint):
        aFactor = 16

        aX = thePoint.x()
        aY = thePoint.y()

        if theDelta.y() > 0:
            aX += aFactor
            aY += aFactor
        else:
            aX -= aFactor
            aY -= aFactor

        self.view.zoom(thePoint.x(), thePoint.y(), aX, aY)

    def onMouseMove(self, theFlags, thePoint):
        # print("UnboundWidget::onMouseMove")
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
                self.view.start_rotation(thePoint.x(), thePoint.y(), 1)
            self.alt_pressed = True
        else:
            self.alt_pressed = False

        # if not self.nointersect and not self.mousedown:
        # 	ip = self.view.intersect_point(thePoint.x(), thePoint.y())
        # 	self.intersectPointSignal.emit(ip)

        if theFlags & Qt.LeftButton or self.alt_pressed:
            if self.orient_mode == 1:
                self.phi -= mv.x() * 0.01
                self.psi += mv.y() * 0.01
                if self.psi > math.pi * 0.4999:
                    self.psi = math.pi * 0.4999
                if self.psi < -math.pi * 0.4999:
                    self.psi = -math.pi * 0.4999
                self.set_orient1()

            if self.orient_mode == 2:
                self.view.rotation(thePoint.x(), thePoint.y())

        elif theFlags & Qt.RightButton or self.shift_pressed:
            self.view.pan(mv.x(), -mv.y())

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

    def pageDownKeyHandler(self):
        x = self.width() / 2
        y = self.height() / 2
        factor = 16
        self.view.zoom(x, y, x - factor, y - factor)

    def pageUpKeyHandler(self):
        x = self.width() / 2
        y = self.height() / 2
        factor = 16
        self.view.zoom(x, y, x + factor, y + factor)

    def keyPressEvent(self, event):
        # if event.key() == Qt.Key_Q:
        # 	self.marker1 = self.view.intersect_point(self.lastPosition.x(), self.lastPosition.y())
        # 	x = self.marker1[0].x
        # 	y = self.marker1[0].y
        # 	z = self.marker1[0].z
        #
        # 	if self.marker1[1]:
        # 		self.mw.marker1Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
        # 		print("Q: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(x,y,z))
        # 	else:
        # 		self.mw.marker1Label.setText(QMARKER_MESSAGE)
        # 	self.mw.updateDistLabel()
        #
        # 	if self.showmarkers:
        # 		disable_lazy()
        # 		self.MarkerQController.set_location(zencad.translate(x,y,z))
        # 		restore_lazy()
        # 		self.MarkerQController.hide(not self.marker1[1])
        # 		self.view.redraw()
        #
        # if event.key() == Qt.Key_W:
        # 	self.marker2 = self.view.intersect_point(self.lastPosition.x(), self.lastPosition.y())
        # 	x = self.marker2[0].x
        # 	y = self.marker2[0].y
        # 	z = self.marker2[0].z
        #
        # 	if self.marker2[1]:
        # 		self.mw.marker2Label.setText("x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x,y,z))
        # 		print("W: x:{0:8.3f},  y:{1:8.3f},  z:{2:8.3f} -> point3({0:.3f},{1:.3f},{2:.3f})".format(x,y,z))
        # 	else:
        # 		self.mw.marker2Label.setText(WMARKER_MESSAGE)
        # 	self.mw.updateDistLabel()
        #
        # 	if self.showmarkers:
        # 		disable_lazy()
        # 		self.MarkerWController.set_location(zencad.translate(x,y,z))
        # 		restore_lazy()
        # 		self.MarkerWController.hide(not self.marker2[1])
        # 		self.view.redraw()

        if event.key() == Qt.Key_PageDown:
            self.pageDownKeyHandler()

        elif event.key() == Qt.Key_PageUp:
            self.pageUpKeyHandler()

        elif event.key() == Qt.Key_M:
            if self.orient_mode == 1:
                self.set_orient_mode(2)
                self.orient_mode_changed_signal.emit(2)
            elif self.orient_mode == 2:
                self.set_orient_mode(1)
                self.orient_mode_changed_signal.emit(1)

        # elif event.key() == Qt.Key_F11:
        # 	if self.isFullScreen():
        # 		self.showNormal()
        # 	else:
        # 		self.showFullScreen()

    def doscreen(self, path):
        import zencad.visual

        q = self.size()
        x, y = q.width(), q.height()
        zencad.visual.screen_view(self.view, path, (x, y))


# def start_viewadapter(scn, connect=None):
# 	wdg = GeometryWidget(scn, connect=connect)
# 	return wdg


def start_widget(scn):
    wdg = GeometryWidget(scn)
    return wdg


# def start_viewadaptor_unbound(connect):
# 	import threading
# 	module_path = zencad.moduledir
# 	thr = threading.Thread(target=lambda: os.system(
# 		"python3 {} --application --bound-apino {} --bound-wid {} --bound-pid {}"
# 		.format(
# 			os.path.join(module_path, "__main__.py"),
# 			*connect)))
# 	thr.start()
#
#
# def start_self(scn):
# 	import zencad
# 	import zencad.opengl
# 	app = QApplication([])
# 	zencad.opengl.init_opengl()
# 	disp = GeometryWidget(scn)
# 	disp.show()
# 	app.exec()
