#!/usr/bin/env python3
"""Keep native preview destruction independent of Python GC's thread."""

import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import traceback
from unittest.mock import patch


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()
    from PyQt5 import QtWidgets, sip
    from zencad import box, render_snapshot
    from zencad.gui.display import DisplayWidget
    from zencad.render import RenderEnvironmentError
    from zencad.scene_draft import SceneDraft
    from OCP.V3d import V3d_View

    draft = SceneDraft(1)
    draft.add(box(20, 12, 8))
    snapshot = draft.snapshot()
    widgets = []
    destroyed = []
    gui_thread = threading.get_ident()

    initialize_driver = DisplayWidget.InitDriver
    context_reported = False

    def track_driver(widget):
        nonlocal context_reported
        # Track before InitDriver, including partially initialized previews.
        widget.destroyed.connect(
            lambda: destroyed.append(threading.get_ident())
        )
        widgets.append(widget)
        initialize_driver(widget)
        if not context_reported:
            from OpenGL.GL import glGetString, GL_VERSION, GL_RENDERER
            from OCP.Graphic3d import Graphic3d_TypeOfLimit_MaxMsaa

            print(
                "OpenGL:", glGetString(GL_VERSION), glGetString(GL_RENDERER),
                "max MSAA:", widget._display._graphic_driver.InquireLimit(
                    Graphic3d_TypeOfLimit_MaxMsaa
                ),
                flush=True,
            )
            context_reported = True

    def verify_cleanup():
        assert widgets
        assert destroyed == [gui_thread] * len(widgets)
        assert all(sip.isdeleted(widget) for widget in widgets)
        assert all(not widget.__dict__ for widget in widgets)
        widgets.clear()
        destroyed.clear()
        # Reproduce the reader thread collecting cycles from an earlier render.
        collector = threading.Thread(target=gc.collect)
        collector.start()
        collector.join(timeout=10)
        assert not collector.is_alive()

    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "preview.png"

            def render_error():
                original = output.read_bytes()
                with patch("zencad.render._apply_display_mode", side_effect=RuntimeError("render failed")):
                    try:
                        render_snapshot(snapshot, output, size=(160, 120))
                    except RenderEnvironmentError as exception:
                        assert "render failed" in str(exception)
                    else:
                        raise AssertionError("render failure was not reported")
                assert output.read_bytes() == original

            def initialization_error(after_binding):
                original = output.read_bytes()
                set_window = V3d_View.SetWindow

                def fail_set_window(view, *args, **kwargs):
                    if after_binding:
                        set_window(view, *args, **kwargs)
                    raise RuntimeError("context creation failed")

                with patch.object(V3d_View, "SetWindow", fail_set_window):
                    try:
                        render_snapshot(snapshot, output, size=(160, 120))
                    except RenderEnvironmentError as exception:
                        assert "context creation failed" in str(exception)
                        assert any(
                            frame.name == "fail_set_window"
                            for frame in traceback.extract_tb(
                                exception.__cause__.__traceback__
                            )
                        )
                        # Keep the failure traceback alive while checking that
                        # native objects are disposed and worker GC is safe.
                        verify_cleanup()
                    else:
                        raise AssertionError("initialization failure was not reported")
                assert output.read_bytes() == original

            with patch.object(DisplayWidget, "InitDriver", track_driver):
                # First exercise a QApplication owned by render_snapshot itself.
                render_snapshot(snapshot, output, size=(160, 120))
                assert QtWidgets.QApplication.instance() is None
                verify_cleanup()
                for after_binding in (False, True):
                    initialization_error(after_binding)
                    assert QtWidgets.QApplication.instance() is None
                render_error()
                assert QtWidgets.QApplication.instance() is None
                verify_cleanup()

                application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
                application.setQuitOnLastWindowClosed(True)
                for after_binding in (False, True):
                    initialization_error(after_binding)
                    assert QtWidgets.QApplication.instance() is application
                    assert application.quitOnLastWindowClosed()
                for fail in (False, True, False):
                    if fail:
                        render_error()
                    else:
                        render_snapshot(snapshot, output, size=(160, 120))
                    verify_cleanup()
                    assert QtWidgets.QApplication.instance() is application
                    assert application.quitOnLastWindowClosed()
                application.quit()
    finally:
        gc.collect()
        if gc_was_enabled:
            gc.enable()
    print("ZenCad render lifecycle smoke: OK")


if __name__ == "__main__":
    main()
