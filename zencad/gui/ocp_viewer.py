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
        self._closed = False

    @staticmethod
    def _native_handle_capsule(window_handle):
        """Wrap a Qt native pointer without transferring its ownership."""
        if hasattr(window_handle, "ascapsule"):
            return window_handle.ascapsule()

        py_capsule_new = ctypes.pythonapi.PyCapsule_New
        py_capsule_new.restype = ctypes.py_object
        py_capsule_new.argtypes = (
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
        )
        return py_capsule_new(
            ctypes.c_void_p(int(window_handle)), None, None
        )

    def _create_native_window(self, window_handle, parent):
        if sys.platform.startswith("linux"):
            from OCP.Xw import Xw_Window

            return Xw_Window(self._display_connection, int(window_handle))

        if sys.platform.startswith("win"):
            from OCP.WNT import WNT_Window

            # Qt exposes HWND as an integer, while OCP's pybind11 wrapper
            # models native pointer arguments as PyCapsules.
            return WNT_Window(self._native_handle_capsule(window_handle))

        if sys.platform == "darwin":
            from OCP.Cocoa import Cocoa_Window

            # QWidget.winId() is the NSView pointer on macOS. Cocoa_Window is
            # OCCT's native adapter for embedding a view into that widget.
            return Cocoa_Window(self._native_handle_capsule(window_handle))

        # Keep a neutral adapter for any future platform port.
        window = Aspect_NeutralWindow()
        window.SetNativeHandle(int(window_handle))
        if parent is not None:
            window.SetSize(parent.width(), parent.height())
        return window

    def Create(self, window_handle, parent=None):
        if self._closed:
            raise RuntimeError("Cannot recreate a closed OCCT viewer")
        self._parent = parent
        self._window = self._create_native_window(window_handle, parent)
        self.View.SetWindow(self._window)
        if not self._window.IsMapped():
            self._window.Map()

    def Close(self):
        """Release OCCT view resources while its native window still exists."""
        if self._closed:
            return False
        self._closed = True
        try:
            self.Context.RemoveAll(False)
        finally:
            # V3d_View.Remove() destroys the underlying Graphic3d/OpenGL view.
            # Leaving this to Python finalization is too late: Qt may already
            # have destroyed the X11 drawable needed by glXMakeCurrent().
            try:
                self.View.Remove()
            finally:
                self._graphic_driver.ReleaseContext()
                self._window = None
                self._parent = None
        return True

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
