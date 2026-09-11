#!/usr/bin/env python3
"""Keep native preview destruction independent of Python GC's thread."""

import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from unittest.mock import patch


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()
    from PyQt5 import QtWidgets, sip
    from zencad import box, render_snapshot
    from zencad.gui.display import DisplayWidget
    from zencad.render import RenderEnvironmentError
    from zencad.scene_draft import SceneDraft

    draft = SceneDraft(1)
    draft.add(box(20, 12, 8))
    snapshot = draft.snapshot()
    widgets = []
    destroyed = []
    gui_thread = threading.get_ident()

    def track_widget(*args, **kwargs):
        widget = DisplayWidget(*args, **kwargs)
        widget.destroyed.connect(
            lambda: destroyed.append(threading.get_ident())
        )
        widgets.append(widget)
        return widget

    def verify_cleanup():
        assert widgets
        assert destroyed == [gui_thread] * len(widgets)
        assert all(sip.isdeleted(widget) for widget in widgets)
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

            with patch("zencad.gui.display.DisplayWidget", side_effect=track_widget):
                # First exercise a QApplication owned by render_snapshot itself.
                render_snapshot(snapshot, output, size=(160, 120))
                assert QtWidgets.QApplication.instance() is None
                verify_cleanup()
                render_error()
                assert QtWidgets.QApplication.instance() is None
                verify_cleanup()

                application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
                application.setQuitOnLastWindowClosed(True)
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
