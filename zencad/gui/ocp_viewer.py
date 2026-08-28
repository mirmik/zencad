"""Small OCP viewer facade used by ZenCad's Qt widget.

cadquery-ocp exposes OCCT's native viewer classes but intentionally does not
ship pythonocc's ``OCC.Display.OCCViewer`` helpers.  This module implements
only the operations used by ZenCad.
"""

import ctypes
import sys

from OCP.AIS import AIS_InteractiveContext
from OCP.Aspect import Aspect_DisplayConnection, Aspect_NeutralWindow
from OCP.OpenGl import OpenGl_GraphicDriver
from OCP.V3d import V3d_Viewer


class Viewer3d:
    def __init__(self):
        self._display_connection = Aspect_DisplayConnection()
        self._graphic_driver = OpenGl_GraphicDriver(
            self._display_connection
        )
        self.Viewer = V3d_Viewer(self._graphic_driver)
        self.View = self.Viewer.CreateView()
        self.Context = AIS_InteractiveContext(self.Viewer)
        self._window = None
        self._parent = None

    def _create_native_window(self, window_handle, parent):
        if sys.platform.startswith("linux"):
            from OCP.Xw import Xw_Window

            return Xw_Window(self._display_connection, window_handle)

        if sys.platform.startswith("win"):
            from OCP.WNT import WNT_Window

            # Qt exposes HWND as an integer, while OCP's pybind11 wrapper
            # intentionally models native pointer arguments as PyCapsules.
            # Wrap the existing HWND without taking ownership of it.
            py_capsule_new = ctypes.pythonapi.PyCapsule_New
            py_capsule_new.restype = ctypes.py_object
            py_capsule_new.argtypes = (
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_void_p,
            )
            handle_capsule = py_capsule_new(
                ctypes.c_void_p(window_handle), None, None
            )
            return WNT_Window(handle_capsule)

        # Aspect_NeutralWindow is the portable native-handle adapter used by
        # OCCT on platforms where the binding has no dedicated window module.
        window = Aspect_NeutralWindow()
        window.SetNativeHandle(window_handle)
        if parent is not None:
            window.SetSize(parent.width(), parent.height())
        return window

    def Create(self, window_handle, parent=None):
        self._parent = parent
        self._window = self._create_native_window(window_handle, parent)
        self.View.SetWindow(self._window)
        if not self._window.IsMapped():
            self._window.Map()

    def Repaint(self):
        self.View.Redraw()

    def FitAll(self):
        self.View.ZFitAll()
        self.View.FitAll()

    def Rotation(self, x, y):
        self.View.Rotation(x, y)

    def DynamicZoom(self, x1, y1, x2, y2):
        self.View.Zoom(x1, y1, x2, y2)

    def ZoomFactor(self, factor):
        self.View.SetZoom(factor)

    def ZoomArea(self, x1, y1, x2, y2):
        self.View.WindowFit(x1, y1, x2, y2)

    def StartRotation(self, x, y):
        self.View.StartRotation(x, y)

