#!/usr/bin/env python3

import sys
import threading
import math
import time
import os

from OCP.AIS import AIS_Axis, AIS_Shaded, AIS_Shape
from OCP.Aspect import Aspect_GFM_VER
from OCP.Quantity import Quantity_TOC_RGB, Quantity_Color
from OCP.Geom import Geom_Line
from OCP.gp import gp_Ax1, gp_Lin, gp_Pnt, gp_Dir, gp_XYZ
from OCP.Graphic3d import Graphic3d_Camera
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.Aspect import Aspect_TOD_ABSOLUTE

from zencad.gui import ocp_viewer
from zencad.occ_compat import confusion
from zencad.util import point3, to_Pnt
from zencad.geombase import vector3, point3
from zencad.interactive import AxisInteractiveObject, ShapeInteractiveObject
import zencad.color as color
from zencad.axis import Axis
import zencad.geom.trans
import zencad.geom.solid
from zencad.settings import Settings, normalize_msaa_samples
from zencad.gui.navigation import (
    navigation_drag_action,
    normalize_navigation_scheme,
    normalized_custom_bindings,
    wheel_zoom_factor,
)
from zencad.gui.scene_presenter import ScenePresenter

from OpenGL.GL import GL_RGBA, GL_UNSIGNED_BYTE, glReadPixels
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

STARTED_YAW = math.pi * (7 / 16)
STARTED_PITCH = math.pi * -0.15


class BaseViewer(QtOpenGL.QGLWidget):
    ''' The base Qt Widget for an OCC viewer
    '''

    def __init__(self, parent=None):
        fmt = QtOpenGL.QGLFormat()
        super().__init__(fmt, parent=parent)
        # OCCT embeds into this widget's own native child window. Declare that
        # relationship before winId() is created; wrapping the resulting XID
        # in a second QWindow used to cause BadWindow/reparenting races.  A
        # parentless standalone viewer must remain a real top-level window so
        # Qt emits lastWindowClosed and stops its application event loop.
        if parent is not None:
            self.setWindowFlag(QtCore.Qt.SubWindow, True)

        self._display = ocp_viewer.Viewer3d()
        Settings.restore()
        self.set_msaa_samples(
            Settings.get(["view", "msaa_samples"]),
            redraw=False,
        )
        self._inited = False
        self._close_callbacks = []

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

    def set_background_gradient(self, color1, color2):
        qcolor1 = color1.to_Quantity_Color()
        qcolor2 = color2.to_Quantity_Color()
        self._display.View.SetBgGradientColors(
            qcolor1, qcolor2, Aspect_GFM_VER, True)

    def set_background_color(self, color):
        self.set_background_gradient(color, color)

    def set_msaa_samples(self, samples, redraw=True):
        samples = normalize_msaa_samples(samples)
        self._display.View.ChangeRenderingParams().NbMsaaSamples = samples
        self.msaa_samples = samples
        if redraw and self._display._window is not None:
            self._display.View.Redraw()
        return samples

    def close_viewer(self):
        return self._display.Close()

    def add_close_callback(self, callback):
        if not callable(callback):
            raise TypeError("Close callback must be callable")
        self._close_callbacks.append(callback)

    def closeEvent(self, event):
        callbacks, self._close_callbacks = self._close_callbacks, []
        for callback in callbacks:
            callback()
        self.close_viewer()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._display._window is not None and not self._display._closed:
            self._display.View.MustBeResized()

    def paintEngine(self):
        return None


class DisplayWidget(BaseViewer):
    def __init__(self,
                 axis_triedron=True,
                 parent=None):

        super().__init__(parent=parent)
        self.reload_navigation_settings()
        self.View = self._display.View
        self.Viewer = self._display.Viewer
        self.Context = self._display.Context

        # A child viewer receives its final native window only when the full
        # parent hierarchy is shown. Standalone viewers have no such reparent.
        self.init_driver_in_constructor = parent is None
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
        self._first_shape = None
        self.mousedown = False
        self.keyboard_retranslate_mode = False
        self.tracking_mode = False
        self._input_event_sink = None
        self._viewer_event_sink = None

        self.last_redraw = time.time()
        self.animate_updated = threading.Event()

        self.reset_orient1()

        self.make_axis_triedron()
        if axis_triedron:
            self.enable_axis_triedron(True)

        self.camera_center_axes = (
            AxisInteractiveObject(Axis(1, 0, 0), zencad.color.Color.red),
            AxisInteractiveObject(Axis(0, 1, 0), zencad.color.Color.green),
            AxisInteractiveObject(Axis(0, 0, 1), zencad.color.Color.blue)
        )
        for iobj in self.camera_center_axes:
            self.Context.Display(iobj.ais_object, False)
            iobj.bind_context(self.Context, update=False)

        self.msphere = zencad.geom.solid._sphere(1)
        self.MarkerQController = ShapeInteractiveObject(
            self.msphere, color=zencad.color.Color(1, 0, 0))
        self.MarkerWController = ShapeInteractiveObject(
            self.msphere, color=zencad.color.Color(0, 1, 0))
        self.Context.Display(self.MarkerWController.ais_object, False)
        self.Context.Display(self.MarkerQController.ais_object, False)
        self.MarkerQController.bind_context(self.Context, update=False)
        self.MarkerWController.bind_context(self.Context, update=False)
        self.MarkerWController.hide(True)
        self.MarkerQController.hide(True)
        self.set_center_visible(False)

        if self.init_driver_in_constructor:
            self.InitDriver()

        self.scene_presenter = ScenePresenter(self)

    def set_input_event_sink(self, sink):
        if sink is not None and not callable(sink):
            raise TypeError("Input event sink must be callable")
        self._input_event_sink = sink

    def set_viewer_event_sink(self, sink):
        if sink is not None and not callable(sink):
            raise TypeError("Viewer event sink must be callable")
        self._viewer_event_sink = sink

    def _emit_viewer_event(self, event_type, data):
        if self._viewer_event_sink is not None:
            self._viewer_event_sink(event_type, data)

    def _emit_input_event(self, message_type, data):
        if self._input_event_sink is not None:
            return self._input_event_sink(message_type, data)
        return False

    @staticmethod
    def _input_modifiers(modifiers):
        values = []
        for flag, name in (
            (QtCore.Qt.ShiftModifier, "shift"),
            (QtCore.Qt.ControlModifier, "control"),
            (QtCore.Qt.AltModifier, "alt"),
            (QtCore.Qt.MetaModifier, "meta"),
        ):
            if modifiers & flag:
                values.append(name)
        return values

    @staticmethod
    def _input_buttons(buttons):
        values = []
        for flag, name in (
            (QtCore.Qt.LeftButton, "left"),
            (QtCore.Qt.MidButton, "middle"),
            (QtCore.Qt.RightButton, "right"),
            (QtCore.Qt.BackButton, "back"),
            (QtCore.Qt.ForwardButton, "forward"),
        ):
            if buttons & flag:
                values.append(name)
        return values

    @staticmethod
    def _input_button(button):
        values = DisplayWidget._input_buttons(button)
        return values[0] if values else None

    @staticmethod
    def _input_key(event):
        key = event.key()
        if QtCore.Qt.Key_A <= key <= QtCore.Qt.Key_Z:
            return chr(key).lower()
        if QtCore.Qt.Key_0 <= key <= QtCore.Qt.Key_9:
            return chr(key)
        special = {
            QtCore.Qt.Key_Left: "left",
            QtCore.Qt.Key_Right: "right",
            QtCore.Qt.Key_Up: "up",
            QtCore.Qt.Key_Down: "down",
            QtCore.Qt.Key_Space: "space",
            QtCore.Qt.Key_Escape: "escape",
            QtCore.Qt.Key_Enter: "enter",
            QtCore.Qt.Key_Return: "return",
            QtCore.Qt.Key_Tab: "tab",
            QtCore.Qt.Key_Backtab: "backtab",
            QtCore.Qt.Key_Backspace: "backspace",
            QtCore.Qt.Key_Delete: "delete",
            QtCore.Qt.Key_Insert: "insert",
            QtCore.Qt.Key_Home: "home",
            QtCore.Qt.Key_End: "end",
            QtCore.Qt.Key_PageUp: "page_up",
            QtCore.Qt.Key_PageDown: "page_down",
            QtCore.Qt.Key_Shift: "shift",
            QtCore.Qt.Key_Control: "control",
            QtCore.Qt.Key_Alt: "alt",
            QtCore.Qt.Key_Meta: "meta",
        }
        if key in special:
            return special[key]
        if QtCore.Qt.Key_F1 <= key <= QtCore.Qt.Key_F35:
            return "f{}".format(key - QtCore.Qt.Key_F1 + 1)
        rendered = QtGui.QKeySequence(key).toString().strip().lower()
        return rendered or "key:{}".format(key)

    def assert_gui_thread(self):
        if QtCore.QThread.currentThread() != self.thread():
            raise RuntimeError("Scene snapshots must be applied on the GUI thread")

    def apply_snapshot(self, snapshot):
        return self.scene_presenter.apply(snapshot)

    def apply_scene_patch(self, patch):
        return self.scene_presenter.apply_patch(patch)

    def set_navigation_scheme(self, scheme):
        self.navigation_scheme = normalize_navigation_scheme(scheme)
        return self.navigation_scheme

    def reload_navigation_settings(self):
        self.set_navigation_scheme(
            Settings.get(["view", "navigation_scheme"])
        )
        self.navigation_custom_bindings = normalized_custom_bindings({
            "rotate": Settings.get(["view", "navigation_rotate"]),
            "pan": Settings.get(["view", "navigation_pan"]),
            "zoom": Settings.get(["view", "navigation_zoom"]),
        })
        self.navigation_invert_wheel = bool(
            Settings.get(["view", "navigation_invert_wheel"])
        )
        self.navigation_invert_orbit = bool(
            Settings.get(["view", "navigation_invert_orbit"])
        )
        return self.navigation_scheme

    def set_perspective(self, en):
        self._perspective_mode = en
        if en:
            self._display.View.Camera().SetProjectionType(
                Graphic3d_Camera.Projection_Perspective)
        else:
            self._display.View.Camera().SetProjectionType(
                Graphic3d_Camera.Projection_Orthographic)

        self.redraw()

    def reset_topprojection(self):
        self._orient = 1
        self.yaw = math.pi / 2
        self.pitch = -math.pi / 2
        self.set_orient1()
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

    def set_eye(self, pnt, orthogonal=True, redraw=False):
        self._display.View.Camera().SetEye(gp_Pnt(pnt.x, pnt.y, pnt.z))

        if orthogonal:
            self.set_orthogonal()

        self.update_orient1_from_view()
        self.set_orient1()

        if redraw:
            self.redraw()

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

    def set_center(self, pnt, redraw=True):
        self._display.View.Camera().SetCenter(to_Pnt(pnt))
        self.set_orient1()

        if redraw:
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
        self.x_axis = AIS_Axis(gp_Ax1(gp_Pnt(), gp_Dir(1, 0, 0)))
        self.y_axis = AIS_Axis(gp_Ax1(gp_Pnt(), gp_Dir(0, 1, 0)))
        self.z_axis = AIS_Axis(gp_Ax1(gp_Pnt(), gp_Dir(0, 0, 1)))
        self.x_axis.SetColor(Quantity_Color(1, 0, 0, Quantity_TOC_RGB))
        self.y_axis.SetColor(Quantity_Color(0, 1, 0, Quantity_TOC_RGB))
        self.z_axis.SetColor(Quantity_Color(0, 0, 1, Quantity_TOC_RGB))

    def attach_scene(self, scene):
        scene.display = self
        box = scene.boundbox()
        self.scene_max0 = max(box.xlength(), box.ylength(), box.zlength())

        if self._first_shape is None:
            for iobj in scene.interactives:
                if isinstance(iobj, ShapeInteractiveObject):
                    self._first_shape = iobj.shape
                    break

        for iobj in scene.interactives:
            self.Context.Display(iobj.ais_object, False)
            iobj.bind_context(self.Context)

        self.autoscale()

    def remove_all(self):
        self._display.Context.RemoveAll(True)

    def display_interactive_object(self, iobj):
        self.Context.Display(iobj.ais_object, False)
        iobj.bind_context(self.Context)

    def autoscale(self, koeff=0.07, redraw=True):
        self.View.FitAll(koeff)
        if redraw:
            self.redraw()

    def enable_axis_triedron(self, en):
        if en:
            self.Context.Display(self.x_axis, False)
            self.Context.Display(self.y_axis, False)
            self.Context.Display(self.z_axis, False)
        else:
            self.Context.Erase(self.x_axis, False)
            self.Context.Erase(self.y_axis, False)
            self.Context.Erase(self.z_axis, False)
        self.redraw()

    def enable_axis_biedron(self, en, colors=None):
        if en:
            self.Context.Display(self.x_axis, False)
            self.Context.Display(self.y_axis, False)
        else:
            self.Context.Erase(self.x_axis, False)
            self.Context.Erase(self.y_axis, False)

        if colors is not None:
            self.x_axis.SetColor(colors[0].to_Quantity_Color())
            self.y_axis.SetColor(colors[1].to_Quantity_Color())
        self.redraw()

    def restore_location(self, dct, redraw=True):
        scale = dct["scale"]
        eye = point3(dct["eye"])
        center = point3(dct["center"])

        self.set_center(center, redraw=False)
        self.set_eye(eye)
        self.set_scale(scale)
        if redraw:
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
        for c in self.camera_center_axes:
            c.relocate(zencad.geom.trans.translate(self.center()))

    def InitDriver(self):
        if self._display._window is None:
            self._display.Create(window_handle=self.winId(), parent=self)
            self._display.View.MustBeResized()

        self.Viewer.SetDefaultLights()
        self.Viewer.SetLightOn()
        self.Context.SetDisplayMode(AIS_Shaded, False)

        # showEvent runs while Qt is still mapping the parent hierarchy.
        # NVIDIA GLX can block indefinitely if OCCT redraws synchronously at
        # this point, so publish the first frame on the next event-loop turn.
        self.autoscale(redraw=False)
        self.MarkerWController.hide(True)
        self.MarkerQController.hide(True)
        QtCore.QTimer.singleShot(0, self.redraw)

    def redraw_marker(self, qw, x, y, z):
        if qw == "q":
            marker = self.MarkerQController
        elif qw == "w":
            marker = self.MarkerWController

        marker.relocate(zencad.translate(x, y, z))
        marker.hide(x == 0 and y == 0 and z == 0)

        self.redraw()

    def markerQPressed(self):
        self.marker1 = self.intersect_point(
            self.lastPosition[0], self.lastPosition[1]
        )
        x = self.marker1[0].x
        y = self.marker1[0].y
        z = self.marker1[0].z

        self._emit_viewer_event("qmarker", {"x": x, "y": y, "z": z})
        self.redraw_marker("q", x, y, z)

    def markerWPressed(self):
        self.marker2 = self.intersect_point(
            self.lastPosition[0], self.lastPosition[1]
        )
        x = self.marker2[0].x
        y = self.marker2[0].y
        z = self.marker2[0].z

        self._emit_viewer_event("wmarker", {"x": x, "y": y, "z": z})
        self.redraw_marker("w", x, y, z)

    def keyPressEvent(self, event):
        self._emit_input_event("key_down", {
            "key": self._input_key(event),
            "text": event.text(),
            "modifiers": self._input_modifiers(event.modifiers()),
            "repeat": event.isAutoRepeat(),
        })
        MOVE_SCALE = 0.03
        modifiers = event.modifiers()  # QApplication.keyboardModifiers()

        if event.key() == QtCore.Qt.Key_F3:
            self.markerQPressed()
            return

        elif event.key() == QtCore.Qt.Key_F4:
            self.markerWPressed()
            return

        elif event.key() == QtCore.Qt.Key_F5:
            self.move_forw(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_F6:
            self.move_back(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_F8:
            self.autoscale()
            return

        elif event.key() == QtCore.Qt.Key_PageUp:
            self.zoom_up()
            return

        elif event.key() == QtCore.Qt.Key_PageDown:
            self.zoom_down()
            return

        elif event.key() == QtCore.Qt.Key_W and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_forw(MOVE_SCALE)
            return
        elif event.key() == QtCore.Qt.Key_S and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_back(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_D and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_right(MOVE_SCALE)
            return
        elif event.key() == QtCore.Qt.Key_A and (self.mousedown or self.keyboard_retranslate_mode is False):
            self.move_left(MOVE_SCALE)
            return

        elif event.key() == QtCore.Qt.Key_Alt:
            self.temporary1 = self.mapFromGlobal(QtGui.QCursor.pos())
            return

        elif event.key() == QtCore.Qt.Key_Shift:
            ev = self.mapFromGlobal(QtGui.QCursor.pos())
            self.dragStartPosX = ev.x()
            self.dragStartPosY = ev.y()
            return

    def keyReleaseEvent(self, event):
        self._emit_input_event("key_up", {
            "key": self._input_key(event),
            "text": event.text(),
            "modifiers": self._input_modifiers(event.modifiers()),
            "repeat": event.isAutoRepeat(),
        })

    def zoom_factor(self, factor):
        self._display.ZoomFactor(factor)

    def zoom_up(self):
        self.zoom_factor(1.07)

    def zoom_down(self):
        self.zoom_factor(1/1.07)

    def focusInEvent(self, event):
        if self._inited1:
            self._display.Repaint()

    def focusOutEvent(self, event):
        if self._inited1:
            self._display.Repaint()

    def showEvent(self, event):
        if not self._inited0:
            self._inited0 = True

            if not self.init_driver_in_constructor:
                self.InitDriver()

    def paintEvent(self, event):
        if self._display._closed:
            return
        if not self._inited1:
            self._inited1 = True

        self._display.Context.UpdateCurrentViewer()

    def wheelEvent(self, event):
        delta_point = event.angleDelta()
        position = event.pos()
        self._emit_input_event("mouse_wheel", {
            "dx": delta_point.x(),
            "dy": delta_point.y(),
            "x": position.x(),
            "y": position.y(),
            "modifiers": self._input_modifiers(event.modifiers()),
        })
        zoom_factor = wheel_zoom_factor(
            delta_point.y(),
            inverted=self.navigation_invert_wheel,
        )
        self._display.ZoomFactor(zoom_factor)
        self.location_changed_handle()

    def mousePressEvent(self, event):
        button = self._input_button(event.button())
        if button is not None:
            self._emit_input_event("mouse_button_down", {
                "button": button,
                "x": event.x(),
                "y": event.y(),
                "modifiers": self._input_modifiers(event.modifiers()),
            })
        self.setFocus()
        ev = event.pos()
        self.dragStartPosX = ev.x()
        self.dragStartPosY = ev.y()
        self._display.StartRotation(self.dragStartPosX, self.dragStartPosY)
        self.temporary1 = event.pos()
        self.mousedown = True

    def mouseReleaseEvent(self, event):
        button = self._input_button(event.button())
        if button is not None:
            self._emit_input_event("mouse_button_up", {
                "button": button,
                "x": event.x(),
                "y": event.y(),
                "modifiers": self._input_modifiers(event.modifiers()),
            })
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

    def redraw(self):
        self.animate_updated.clear()
        if self._display._closed or self._display._window is None:
            self.animate_updated.set()
            return
        # A splitter can settle after the child's first showEvent without
        # delivering another resize event to the already native OCCT window.
        # Synchronizing here is cheap and guarantees the GL viewport matches
        # the visible widget before every explicit frame.
        self._display.View.MustBeResized()
        self._display.View.Redraw()
        self.last_redraw = time.time()
        self.animate_updated.set()

    def continuous_redraw(self):
        """Этот слот использует поток анимации для обновления
        виджета"""

        if time.time() - self.last_redraw > 0.012:
            self.redraw()
        else:
            self.animate_updated.set()

    def viewline(self, x, y):
        Xv, Yv, Zv, Vx, Vy, Vz = self.View.ConvertWithProj(x, y)
        return gp_Lin(gp_Pnt(Xv, Yv, Zv), gp_Dir(Vx, Vy, Vz))

    def Select(self, X, Y):
        self.Context.MoveTo(X, Y, self.View, False)

        self.Context.Select(False)
        self.Context.InitSelected()

        self.selected_shapes = []
        self.selected_ishapes = []
        if self.Context.MoreSelected():
            if self.Context.HasSelectedShape():
                self.selected_shapes.append(self.Context.SelectedShape())
                self.selected_ishapes.append(
                    self.Context.SelectedInteractive())

        # disable selection for prevent hilighting
        self.Context.ClearSelected(False)

    def intersect_point(self, x, y):
        self.Select(x, y)

        viewLine = self.viewline(x, y)

        for i in range(len(self.selected_shapes)):
            hShape = self.selected_ishapes[i]
            shape = self.selected_shapes[i]

            loc = self.Context.Location(hShape)
            loc_shape = shape.Located(loc)

            shapeIntersector = IntCurvesFace_ShapeIntersector()
            shapeIntersector.Load(loc_shape, confusion())
            shapeIntersector.Perform(viewLine, float("-inf"), float("+inf"))

            if shapeIntersector.NbPnt() >= 1:
                ip = shapeIntersector.Pnt(1)
                return point3(ip), True
            else:
                continue

        return point3(), False

    def mouseMoveEvent(self, evt):
        self._emit_input_event("mouse_move", {
            "x": evt.x(),
            "y": evt.y(),
            "buttons": self._input_buttons(evt.buttons()),
            "modifiers": self._input_modifiers(evt.modifiers()),
        })
        pt = evt.pos()
        modifiers = evt.modifiers()
        self.lastPosition = (evt.x(), evt.y())

        if self.tracking_mode and not self.mousedown:
            ip, sts = self.intersect_point(evt.x(), evt.y())
            self._emit_viewer_event("trackinfo", (ip.to_tuple(), sts))

        action = navigation_drag_action(
            self.navigation_scheme,
            self._input_buttons(evt.buttons()),
            self._input_modifiers(modifiers),
            self.navigation_custom_bindings,
        )

        if action == "rotate":
            if self._orient == 1:

                mv = evt.pos() - self.temporary1
                self.temporary1 = evt.pos()

                direction = 1 if self.navigation_invert_orbit else -1
                self.yaw += direction * mv.x() * 0.01
                self.pitch += direction * mv.y() * 0.01
                if self.pitch > math.pi * 0.4999:
                    self.pitch = math.pi * 0.4999
                if self.pitch < -math.pi * 0.4999:
                    self.pitch = -math.pi * 0.4999
                self.set_orient1()
                self.continuous_redraw()
            elif self._orient == 2:
                self._display.Rotation(pt.x(), pt.y())

            self.location_changed_handle()

        elif action == "zoom":
            self._display.Repaint()
            self._display.DynamicZoom(abs(self.dragStartPosX),
                                      abs(self.dragStartPosY), abs(pt.x()),
                                      abs(pt.y()))
            self.dragStartPosX = pt.x()
            self.dragStartPosY = pt.y()
            self.location_changed_handle()

        elif action == "pan":
            dx = pt.x() - self.dragStartPosX
            dy = pt.y() - self.dragStartPosY
            self.dragStartPosX = pt.x()
            self.dragStartPosY = pt.y()
            self._display.View.Pan(dx, -dy)
            self.location_changed_handle()

    def _resize_external(self, size):
        if self._inited0:
            self.resize(QtCore.QSize(*size))

    def tracking_mode_enable(self, en):
        self.tracking_mode = en

    def external_communication_command(self, data):
        cmd = data["cmd"]
        try:
            if cmd == "autoscale":
                self.autoscale()
            elif cmd == "resetview":
                self.reset_orient()
            elif cmd == "topprojection":
                self.reset_topprojection()
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
            elif cmd == "save_screenshot":
                self.save_screenshot()
            elif cmd == "console":
                sys.stdout.write(data["data"])
        except Exception as ex:
            print(
                "Error on external command handling:",
                repr(ex),
                file=sys.stderr,
            )

    def move_vector_cross(self, vecin, koeff):
        vec = self.center() - self.eye()
        vec = vec.cross(vecin).normalize() * self.scene_max0
        self.set_center(self.center() + vec * koeff, redraw=False)
        self.location_changed_handle()
        self.redraw()

    def move_vector_eye_line(self, koeff):
        vec = self.center() - self.eye()
        vecnorm = vec.normalize() * self.scene_max0
        self.set_center(self.center() + vecnorm * koeff, redraw=False)
        self.set_eye(self.eye() + vecnorm * koeff, redraw=False)
        self.location_changed_handle()
        self.redraw()

    def move_back(self, koeff=1):
        self.move_vector_eye_line(-koeff)

    def move_forw(self, koeff=1):
        self.move_vector_eye_line(koeff)

    def move_left(self, koeff=1):
        self.move_vector_cross(vector3(0, 0, -1), koeff)

    def move_right(self, koeff=1):
        self.move_vector_cross(vector3(0, 0, 1), koeff)

    def first_person_mode(self):
        self.set_perspective(True)
        self.set_center(self.eye()-vector3(0, 0, 1), redraw=False)
        self.set_center_visible(False)
        self.set_orient1()
        self.redraw()

    def export_file_for_one_shape(self, filters, defaultFilter):
        # if self.scene.total() != 1 + self.count_of_helped_shapes:
        #    print("more/less than one shape in scene:", self.scene.total() - self.count_of_helped_shapes)
        #    return False, "", None

        shape = self._first_shape

        if shape is None:
            raise Exception("Display widget hasn't ShapeInteractiveObject")

        path = QtWidgets.QFileDialog.getSaveFileName(
            self, "STL Export", QtCore.QDir.currentPath(), filters, defaultFilter
        )

        path = path[0]
        return True, path, shape

    def addon_exportstl(self):
        from zencad.convert.api import _to_stl

        ok, path, shape = self.export_file_for_one_shape(
            filters="*.stl;;*.*",
            defaultFilter="*.stl")

        if ok == False or path == "":
            return

        d, okPressed = QtWidgets.QInputDialog.getDouble(
            self, "Get double", "Value:", 0.01, 0, 10, 10
        )

        if not okPressed:
            return

        _to_stl(shape, path, d)
        print("Make STL procedure finished.")

    def addon_exportbrep(self):
        from zencad.convert.api import _to_brep
        ok, path, shape = self.export_file_for_one_shape(
            filters="*.brep;;*.*",
            defaultFilter="*.brep")

        if ok == False or path == "":
            return

        _to_brep(shape, path)
        print("Save BREP procedure finished.")

    def save_screenshot(self):
        filters = "*.png;;*.bmp;;*.jpg;;*.*"
        defaultFilter = "*.png"

        retpath = QtWidgets.QFileDialog.getSaveFileName(
            self, "Dump image", QtCore.QDir.currentPath(), filters, defaultFilter
        )

        path = retpath[0]

        if path == "":
            return

        buf = glReadPixels(0, 0, self.width(), self.height(),
                           GL_RGBA, GL_UNSIGNED_BYTE)

        pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(buf, self.width(), self.height(),
                                                      QtGui.QImage.Format_RGBA8888).mirrored(False, True))

        file = QtCore.QFile(path)
        file.open(QtCore.QIODevice.WriteOnly)
        pixmap.save(file, "PNG")
        # self.screen_saver.set_background(self.last_screen)
        # self.openlock.unlock()

    def addon_to_freecad_action(self):
        from zencad.convert.api import _to_brep
        import tempfile

        # if self.scene.total() != 1 + self.count_of_helped_shapes:
        #    print("more/less than one shape in scene:", self.scene.total() - self.count_of_helped_shapes)
        #    return False, "", None

        tmpfl = tempfile.mktemp(".brep")
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(
            'import Part; export = Part.Shape(); export.read("{}"); Part.show(export); Gui.activeDocument().activeView().viewAxonometric(); Gui.SendMsgToActiveView("ViewFit")'.format(
                tmpfl
            ),
            mode=cb.Clipboard,
        )
        _to_brep(self._first_shape, tmpfl)
        QtWidgets.QMessageBox.information(
            self, self.tr("ToFreeCad"), self.tr(
                "Script copied to clipboard. Don't close gui before script placing.")
        )
