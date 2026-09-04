"""Select a Qt backend compatible with OCCT's native Linux window."""

import os
import sys


def configure_qt_platform(environ=None, platform=None):
    """Use XWayland for the OCP viewer when running in a Wayland session.

    ``OCP.Xw_Window`` expects an X11 window ID.  A Qt Wayland native handle is
    not an XID, so passing it to OCCT produces an X ``BadWindow`` error.  Keep
    explicit user choices intact and select ``xcb`` only for the default
    Linux/Wayland case where XWayland is available through ``DISPLAY``.
    """
    environ = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform

    if "QT_QPA_PLATFORM" in environ:
        return environ["QT_QPA_PLATFORM"]

    if (
        platform.startswith("linux")
        and environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        and environ.get("DISPLAY")
    ):
        environ["QT_QPA_PLATFORM"] = "xcb"
        return "xcb"

    return None
