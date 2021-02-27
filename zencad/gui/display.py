#!/usr/bin/env python3

import sys
import threading
import math
import time
import os

from OCC.Core.AIS import AIS_Axis, AIS_Shaded
from OCC.Core.Aspect import Aspect_GFM_VER
from OCC.Core.Quantity import Quantity_TOC_RGB, Quantity_Color
from OCC.Core.Geom import Geom_Line
from OCC.Core.gp import gp_Lin, gp_Pnt, gp_Dir, gp_XYZ
from OCC.Core.Graphic3d import Graphic3d_Camera
import OCC.Core.BRepPrimAPI

from OCC.Display import OCCViewer
from zencad.util import point3, to_Pnt
from zenframe.util import print_to_stderr
from zencad.interactive_object import AxisInteractiveObject
import zencad.color as color
from zencad.axis import Axis
import zencad.geom.trans

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

STARTED_YAW = math.pi * (7 / 16)
STARTED_PITCH = math.pi * -0.15


class BaseViewer(QtOpenGL.QGLWidget):
    ''' The base Qt Widget for an OCC viewer
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self._display = OCCViewer.Viewer3d()
        self._inited = False

        # enable Mouse Tracking
        self.setMouseTracking(True)

        # Strong focus
        self.setFocusPolicy(QtCore.Qt.WheelFocus)

        self.setAttribute(QtCore.Qt.WA_NativeWindow)
        self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        self.setAutoFillBackground(False)

        color1 = Quantity_Color(.55, .55, .55, Quantity_TOC_RGB)
        color2 = Quantity_Color(.22, .22, .22, Quantity_TOC_RGB)
        self._display.View.SetBgGradientColors(
            color1, color2, Aspect_GFM_VER, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._display.View.MustBeResized()

    def paintEngine(self):
        return None


class DisplayWidget(BaseViewer):
    def __init__(self,
                 axis_triedron=True,
                 communicator=None):

        super().__init__()

        self._communicator = communicator
        self._orient = 1
        self._drawbox = False
        self._zoom_area = False
        self._inited0 = False
        self._inited1 = False
        self._leftisdown = False
        self._middleisdown = False
        self._rightisdown = False
        self._drawtext = True
        self._perspective_mode = False
        self.mousedown = False
        self.keyboard_retranslate_mode = True

        self.last_redraw = time.time()
        self.animate_updated = threading.Event()

        self.reset_orient1()

        self.make_axis_triedron()
        if axis_triedron:
            self.enable_axis_triedron(True)

        self.camera_center_axes = (
            AxisInteractiveObject(Axis(1, 0, 0), color.red),
            AxisInteractiveObject(Axis(0, 1, 0), color.green),
            AxisInteractiveObject(Axis(0, 0, 1), color.blue)
        )
        for iobj in self.camera_center_axes:
            iobj.bind_context(self._display.GetContext())
            self._display.GetContext().Display(iobj.ais_object, True)

        self.set_center_visible(False)

    def set_perspective(self, en):
        self._perspective_mode = en
        if en:
            self._display.View.Camera().SetProjectionType(
                Graphic3d_Camera.Projection_Perspective)
        else:
            self._display.View.Camera().SetProjectionType(
                Graphic3d_Camera.Projection_Orthographic)

        self.redraw()

    def reset_orient1(self):
        self._orient = 1
        self.yaw = STARTED_YAW
        self.pitch = STARTED_PITCH
        self.set_orient1()
        # self.set_orient1()
        # self.update_orient1_from_view()
        self.redraw()

    def reset_orient2(self):
        self._orient = 2
        self.set_orient2()
        self.redraw()

    def reset_orient(self):
        self.reset_orient1()
        self.autoscale()
        self.redraw()

    def set_orient1(self):

        self._display.View.Camera().SetDirection(gp_Dir(
            math.cos(self.pitch) * math.cos(self.yaw),
            math.cos(self.pitch) * math.sin(self.yaw),
            math.sin(self.pitch)
        ))
        self._display.View.Camera().SetUp(gp_Dir(0, 0, 1))

    def set_orient2(self):
        pass

    def update_orient1_from_view(self):
        """Read actual camera orientation data from view"""
        d = self._display.View.Camera().Direction()
        x, y, z = d.X(), d.Y(), d.Z()
        self.pitch = math.asin(z)
        x = x / math.cos(self.pitch)
        y = y / math.cos(self.pitch)
        self.yaw = math.atan2(y, x)

    def set_orthogonal(self):
        self._display.View.Camera().SetUp(gp_Dir(0, 0, 1))

    def eye(self):
        return point3(self._display.View.Eye())

    def set_eye(self, pnt, orthogonal=True):
        self._display.View.SetEye(pnt.x, pnt.y, pnt.z)

        if orthogonal:
            self.set_orthogonal()

        self.update_orient1_from_view()
        self.set_orient1()

    def set_center_visible(self, en):
        if en:
            # self.camera_center_mark.hide(False)
            self.camera_center_axes[0].hide(False)
            self.camera_center_axes[1].hide(False)
            self.camera_center_axes[2].hide(False)
        else:
            # self.camera_center_mark.hide(True)
            self.camera_center_axes[0].hide(True)
            self.camera_center_axes[1].hide(True)
            self.camera_center_axes[2].hide(True)

        self.redraw()

    def set_center(self, pnt):
        self._display.View.Camera().SetCenter(to_Pnt(pnt))
        self.set_orient1()
        self.redraw()

    def center(self):
        return point3(self._display.View.Camera().Center())

    def scale(self):
        return self._display.View.Camera().Scale()

    def set_scale(self, scl):
        return self._display.View.Camera().SetScale(scl)

    def centering(self):
        self.set_center(point3(0, 0, 0))

    def make_axis_triedron(self):
        self.x_axis = AIS_Axis(
            Geom_Line(gp_Lin(gp_Pnt(0, 0, 0), gp_Dir(gp_XYZ(1, 0, 0)))))
        self.y_axis = AIS_Axis(
            Geom_Line(gp_Lin(gp_Pnt(0, 0, 0), gp_Dir(gp_XYZ(0, 1, 0)))))
        self.z_axis = AIS_Axis(
            Geom_Line(gp_Lin(gp_Pnt(0, 0, 0), gp_Dir(gp_XYZ(0, 0, 1)))))
        self.x_axis.SetColor(Quantity_Color(1, 0, 0, Quantity_TOC_RGB))
        self.y_axis.SetColor(Quantity_Color(0, 1, 0, Quantity_TOC_RGB))
        self.z_axis.SetColor(Quantity_Color(0, 0, 1, Quantity_TOC_RGB))

    def attach_scene(self, scene):
        scene.display = self

        for iobj in scene.interactives:
            iobj.bind_context(self._display.GetContext())
            self._display.GetContext().Display(iobj.ais_object, True)

    def autoscale(self, koeff=0.07):
        self._display.GetView().FitAll(koeff)
        self._display.GetView().Redraw()

    def enable_axis_triedron(self, en):
        if en:
            self._display.GetContext().Display(self.x_axis, True)
            self._display.GetContext().Display(self.y_axis, True)
            self._display.GetContext().Display(self.z_axis, True)
        else:
            self._display.GetContext().Erase(self.x_axis, True)
            self._display.GetContext().Erase(self.y_axis, True)
            self._display.GetContext().Erase(self.z_axis, True)

    def restore_location(self, dct):
        scale = dct["scale"]
        eye = point3(dct["eye"])
        center = point3(dct["center"])

        self.set_center(center)
        self.set_eye(eye)
        self.set_scale(scale)
        self.redraw()

        self.update_orient1_from_view()
        self.location_changed_handle()

    def store_location(self):
        return {
            "scale": self.scale(),
            "eye": self.eye().to_tuple(),
            "center": self.center().to_tuple()
        }

    def location_changed_handle(self):
        # self.camera_center_mark.relocate(pyservoce.translate(*self.view.center()))
        for c in self.camera_center_axes:
            c.relocate(zencad.geom.trans.translate(self.center()))

        if self._communicator:
            loc = self.store_location()
            self._communicator.send({"cmd": "location",  "loc": loc})

    def InitDriver(self):
        self._display.Create(window_handle=int(self.winId()), parent=self)
        # background gradient
#		self._display.SetModeShaded()

        self._display.GetViewer().SetDefaultLights()
        self._display.GetViewer().SetLightOn()

        self._display.GetContext().SetDisplayMode(AIS_Shaded, False)
        self._display.GetContext().DefaultDrawer().SetFaceBoundaryDraw(True)

        self.autoscale()

    def keyPressEvent(self, event):
        MOVE_SCALE = 0.05
        modifiers = event.modifiers()  # QApplication.keyboardModifiers()

        # print(event.key())

        if event.key() == QtCore.Qt.Key_F3:
            self.markerQPressed()
            return

        elif event.key() == QtCore.Qt.Key_F4:
            self.markerWPressed()
            return

        elif event.key() == QtCore.Qt.Key_F5:
            self.move_forw()
            return

        elif event.key() == QtCore.Qt.Key_F6:
            self.move_back()
            return

        elif event.key() == QtCore.Qt.Key_F8:
            self.autoscale()
            return

        elif event.key() == QtCore.Qt.Key_PageUp:
            self.zoom_up(self.zoom_koeff_key)
            return

        elif event.key() == QtCore.Qt.Key_PageDown:
            self.zoom_down(self.zoom_koeff_key)
            return

        elif event.key() == QtCore.Qt.Key_W and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_forw(MOVE_SCALE)
            return
        elif event.key() == QtCore.Qt.Key_S and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_back(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_D and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_left(MOVE_SCALE)
            return
        elif event.key() == QtCore.Qt.Key_A and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_right(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_Alt:
            self.temporary1 = self.mapFromGlobal(QtGui.QCursor.pos())
            return

        elif event.key() == QtCore.Qt.Key_Shift:
            ev = self.mapFromGlobal(QtGui.QCursor.pos())
            self.dragStartPosX = ev.x()
            self.dragStartPosY = ev.y()
            return

        # If signal not handling here, translate it onto top level
        if self._communicator:
            self._communicator.send({
                "cmd": "keypressed_raw",
                "key": event.key(),
                "modifiers": "",
                "text": event.text()})

    def focusInEvent(self, event):
        if self._inited1:
            self._display.Repaint()

    def focusOutEvent(self, event):
        if self._inited1:
            self._display.Repaint()

    def showEvent(self, event):
        if not self._inited0:
            self.InitDriver()

            self._inited0 = True

    def paintEvent(self, event):
        if not self._inited1:

            QtGui.QWindow.fromWinId(self.winId()).setFlags(
                QtGui.QWindow.fromWinId(self.winId()).flags() |
                QtCore.Qt.SubWindow)

            self._inited1 = True

        self._display.Context.UpdateCurrentViewer()

        if self._drawbox:
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))
            rect = QtCore.QRect(*self._drawbox)
            painter.drawRect(rect)

    def wheelEvent(self, event):
        mul = 1.1
        delta = event.angleDelta().y()
        if delta > 0:
            zoom_factor = mul
        else:
            zoom_factor = 1/mul
        self._display.ZoomFactor(zoom_factor)
        self.location_changed_handle()

    def mousePressEvent(self, event):
        self.setFocus()
        ev = event.pos()
        self.dragStartPosX = ev.x()
        self.dragStartPosY = ev.y()
        self._display.StartRotation(self.dragStartPosX, self.dragStartPosY)
        self.temporary1 = event.pos()
        # print(self.temporary1)
        self.mousedown = True

    def mouseReleaseEvent(self, event):
        pt = event.pos()
        modifiers = event.modifiers()

        if event.button() == QtCore.Qt.LeftButton:
            pass

        elif event.button() == QtCore.Qt.RightButton:
            if self._zoom_area:
                [Xmin, Ymin, dx, dy] = self._drawbox
                self._display.ZoomArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
                self._zoom_area = False

        self.mousedown = False

   # def DrawBox(self, event):
  #      tolerance = 2
 #       pt = event.pos()
#        dx = pt.x() - self.dragStartPosX
   #     dy = pt.y() - self.dragStartPosY
  #      if abs(dx) <= tolerance and abs(dy) <= tolerance:
 #           return
#        self._drawbox = [self.dragStartPosX, self.dragStartPosY, dx, dy]

    def redraw(self):
        self.animate_updated.clear()
        self._display.View.Redraw()
        self.last_redraw = time.time()
        self.animate_updated.set()

    def continuous_redraw(self):
        """Этот слот использует поток анимации для обновления
        виджета"""

        if time.time() - self.last_redraw > 0.012:

            # if self.pan_temporary != (0,0):
            #    self.view.pan(self.pan_temporary[0], self.pan_temporary[1])
            #    self.pan_temporary=(0,0)
            self.redraw()
        else:
            self.animate_updated.set()

    def mouseMoveEvent(self, evt):
        pt = evt.pos()
        buttons = int(evt.buttons())
        modifiers = evt.modifiers()

        # ROTATE
        if (buttons == QtCore.Qt.LeftButton or
                modifiers == QtCore.Qt.AltModifier):
            if self._orient == 1:

                mv = evt.pos() - self.temporary1
                self.temporary1 = evt.pos()

                self.yaw -= mv.x() * 0.01
                self.pitch -= mv.y() * 0.01
                if self.pitch > math.pi * 0.4999:
                    self.pitch = math.pi * 0.4999
                if self.pitch < -math.pi * 0.4999:
                    self.pitch = -math.pi * 0.4999
                self.set_orient1()
                # self.location_changed_handle()
                self.continuous_redraw()
            elif self._orient == 2:
                self._display.Rotation(pt.x(), pt.y())

            self.location_changed_handle()

        # DYNAMIC ZOOM
        elif (buttons == QtCore.Qt.MidButton):
            self._display.Repaint()
            self._display.DynamicZoom(abs(self.dragStartPosX),
                                      abs(self.dragStartPosY), abs(pt.x()),
                                      abs(pt.y()))
            self.dragStartPosX = pt.x()
            self.dragStartPosY = pt.y()
            self.location_changed_handle()

        # PAN
        elif (buttons == QtCore.Qt.RightButton or
                modifiers == QtCore.Qt.ShiftModifier):
            dx = pt.x() - self.dragStartPosX
            dy = pt.y() - self.dragStartPosY
            self.dragStartPosX = pt.x()
            self.dragStartPosY = pt.y()
            self._display.View.Pan(dx, -dy)
            self.location_changed_handle()

    def _resize_external(self, size):
        if self._inited0:
            self.resize(QtCore.QSize(*size))

    def external_communication_command(self, data):
        cmd = data["cmd"]
        try:
            if cmd == "autoscale":
                self.autoscale()
            elif cmd == "resetview":
                self.reset_orient()
            elif cmd == "redraw":
                self.redraw()
            elif cmd == "resize":
                self._resize_external(size=(data["size"][0], data["size"][1]))
            elif cmd == "orient1":
                self.reset_orient1()
            elif cmd == "orient2":
                self.reset_orient2()
            elif cmd == "centering":
                self.centering()
            elif cmd == "location":
                self.restore_location(data["loc"])
            elif cmd == "set_perspective":
                self.set_perspective(data["en"])
            elif cmd == "set_center_visible":
                self.set_center_visible(data["en"])
            elif cmd == "first_person_mode":
                self.first_person_mode()
            elif cmd == "exportstl":
                self.addon_exportstl()
            elif cmd == "exportbrep":
                self.addon_exportbrep()
            elif cmd == "to_freecad":
                self.addon_to_freecad_action()
            elif cmd == "tracking":
                self.tracking_mode_enable(data["en"])
            elif cmd == "keyboard_retranslate":
                self.keyboard_retranslate_mode = data["en"]
            elif cmd == "screenshot":
                self.addon_screenshot_upload()
            elif cmd == "console":
                sys.stdout.write(data["data"])
        except Exception as ex:
            print_to_stderr("Error on external command handling", repr(ex))

    def move_back(self, koeff=1):
        print("move_back")
        pass
        #vec = self.view.eye() - self.view.center()
        #vec = vec.normalize() * self.scene_max0
        #self.view.set_center(self.view.center() + vec * koeff)
        #self.view.set_eye(self.view.eye() + vec * koeff)
        # self.location_changed_handle()
        # self.view.redraw()

    def move_forw(self, koeff=1):
        print("move_forw")
        pass
        #scale = self.view.scale()
        #vec = self.view.center() - self.view.eye()
        #vec = vec.normalize() * self.scene_max0
        #self.view.set_center(self.view.center() + vec * koeff)
        #self.view.set_eye(self.view.eye() + vec * koeff)
        # self.location_changed_handle()
        # self.view.redraw()

    def move_right(self, koeff=1):
        print("move_right")
        pass
        #scale = self.view.scale()
        #vec = self.view.center() - self.view.eye()
        #vec = pyservoce.vector3(0,0,1).cross(vec).normalize() * self.scene_max0
        #self.view.set_center(self.view.center() + vec * koeff)
        #self.view.set_eye(self.view.eye() + vec * koeff)
        # self.location_changed_handle()
        # self.view.redraw()

    def move_left(self, koeff=1):
        print("move_left")
        pass
        #scale = self.view.scale()
        #vec = self.view.center() - self.view.eye()
        #vec = pyservoce.vector3(0,0,-1).cross(vec).normalize() * self.scene_max0
        #self.view.set_center(self.view.center() + vec * koeff)
        #self.view.set_eye(self.view.eye() + vec * koeff)
        # self.location_changed_handle()
        # self.view.redraw()
