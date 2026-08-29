#!/usr/bin/env python3
"""Named GUI smoke for managed reload into one persistent viewer."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import mock

RELOAD_COUNT = 20


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtTest, QtWidgets

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from zencad.gui.mainwindow import MainWindow

    with TemporaryDirectory() as temporary_directory:
        script_path = Path(temporary_directory) / "model.py"
        script_path.write_text(
            "from zencad import *\n"
            "from zencad.interactive import arrow\n"
            "print('managed reload')\n"
            "display(box(10))\n"
            "display(point3(15, 0, 0), color=color.red)\n"
            "display(arrow((0, 0, 0), (0, 15, 0), arrlen=2))\n"
            "show()\n",
            encoding="utf-8",
        )
        error_path = Path(temporary_directory) / "error.py"
        error_path.write_text(
            "from zencad import *\n"
            "display(box(30))\n"
            "show()\n"
            "raise RuntimeError('expected reload failure after show')\n",
            encoding="utf-8",
        )
        slow_path = Path(temporary_directory) / "slow.py"
        slow_path.write_text(
            "import time\n"
            "time.sleep(10)\n",
            encoding="utf-8",
        )
        replacement_path = Path(temporary_directory) / "replacement.py"
        replacement_path.write_text(
            "from zencad import *\n"
            "display(sphere(7))\n"
            "show()\n",
            encoding="utf-8",
        )
        animation_path = Path(temporary_directory) / "animation.py"
        animation_path.write_text(
            "from zencad import *\n"
            "controller = display(box(10, center=True))\n"
            "position = 0\n"
            "def animate(state):\n"
            "    global position\n"
            "    if state.input.key_pressed('right'):\n"
            "        position += 15\n"
            "        controller.relocate(translate(position, 0, 0))\n"
            "        controller.set_color(1, 0.4, 0.2, 0)\n"
            "show(animate=animate, animate_step=0.01)\n",
            encoding="utf-8",
        )

        window = MainWindow(restore_gui=False)
        assert window.size().width() == 1100
        assert window.size().height() == 760
        assert "zenframe" not in sys.modules
        display = window.display_widget
        window.resize(800, 600)
        window.show()
        application.processEvents()
        with mock.patch(
            "zencad.gui.actions.QMessageBox.about"
        ) as about_dialog:
            window.aboutAction()
        about_html = about_dialog.call_args.args[2]
        assert "ZenCad version: 2.0.0" in about_html
        assert "2018-2021, 2026" in about_html
        assert window.hsplitter.count() == 2
        assert window.vsplitter.count() == 2
        assert not window.calculation_overlay.active
        assert not window.console.isHidden()
        assert window.vsplitter.sizes()[1] >= 120
        assert display.msaa_samples in (0, 2, 4, 8)
        assert (
            display.View.RenderingParams().NbMsaaSamples
            == display.msaa_samples
        )
        assert not hasattr(window, "mCoordsDiff")
        window.info_widget.set_marker_data("q", 4, 5, 6)
        window.info_widget.set_marker_data("w", 1, 1, 1)
        measurement = window.info_widget.markerDistLabel.text()
        assert "Δ(F3−F4): (3.000, 4.000, 5.000)" in measurement
        assert "Distance: 7.071" in measurement

        native_window = int(display.winId())
        viewer = display.Viewer
        view = display.View
        context = display.Context
        editor = window.texteditor
        console = window.console
        state = {
            "commits": 0,
            "generation": None,
            "camera": None,
            "phase": "reload",
            "target": None,
            "stable_object": None,
            "animation_handle": None,
            "animation_sequence": None,
            "input_sent": False,
        }

        def assert_persistent_viewer():
            assert int(display.winId()) == native_window
            assert display.Viewer is viewer
            assert display.View is view
            assert display.Context is context
            assert window.texteditor is editor
            assert window.console is console

        def assert_visible_frame():
            if sys.platform.startswith("win"):
                display.redraw()
                application.processEvents()
                image_path = Path(temporary_directory) / "viewer.png"
                assert display.View.Dump(str(image_path))
                assert image_path.stat().st_size > 0
                return
            for _attempt in range(5):
                display.redraw()
                QtTest.QTest.qWait(20)
                image = application.primaryScreen().grabWindow(
                    int(display.winId())
                ).toImage()
                colors = {
                    image.pixelColor(x, y).rgb()
                    for x in range(
                        0, image.width(), max(1, image.width() // 16)
                    )
                    for y in range(
                        0, image.height(), max(1, image.height() // 16)
                    )
                }
                if len(colors) > 4:
                    return
            raise AssertionError("viewer framebuffer is blank")

        def start_cancel_case():
            state["phase"] = "cancel"
            state["target"] = window.open(
                str(slow_path), update_texteditor=False
            )
            assert window.calculation_overlay.active
            assert window.calculation_overlay.isVisible()
            application.processEvents()
            if sys.platform.startswith("linux"):
                overlay = window.calculation_overlay
                screen = overlay.screen()
                screenshot = screen.grabWindow(0).toImage()
                sample = overlay.mapToGlobal(QtCore.QPoint(16, 16))
                sample -= screen.geometry().topLeft()
                color = screenshot.pixelColor(sample)
                assert max(color.red(), color.green(), color.blue()) < 90, color
            QtCore.QTimer.singleShot(
                100, window._runner_supervisor.cancel_current
            )

        def poll():
            generation = display.scene_presenter.committed_generation
            if state["phase"] == "reload":
                if generation is None or generation == state["generation"]:
                    return
                state["generation"] = generation
                state["commits"] += 1
                assert len(display.scene_presenter.objects) == 3
                assert [
                    type(item.ais_object).__name__
                    for item in display.scene_presenter.objects
                ] == ["AIS_Shape", "AIS_Point", "AIS_Line"]
                assert_persistent_viewer()

                if state["commits"] == 1:
                    # Keep a deliberately non-default camera while leaving
                    # enough of the model visible in the full-size viewport.
                    display.set_scale(20.0)
                    state["camera"] = display.store_location()
                else:
                    current_camera = display.store_location()
                    assert current_camera == state["camera"], (
                        state["camera"], current_camera
                    )

                if state["commits"] == RELOAD_COUNT:
                    assert_visible_frame()
                    state["stable_object"] = display.scene_presenter.objects[0]
                    state["phase"] = "error"
                    state["target"] = window.open(
                        str(error_path), update_texteditor=False
                    )
                else:
                    window.open(str(script_path), update_texteditor=False)
                return

            status = window._generation_statuses.get(state["target"])
            if state["phase"] == "error" and status == "error":
                assert display.scene_presenter.committed_generation == state["generation"]
                assert display.scene_presenter.objects[0] is state["stable_object"]
                assert display.store_location() == state["camera"]
                assert_persistent_viewer()
                start_cancel_case()
            elif state["phase"] == "cancel" and status == "cancelled":
                assert not window.calculation_overlay.active
                assert display.scene_presenter.committed_generation == state["generation"]
                assert display.scene_presenter.objects[0] is state["stable_object"]
                assert display.store_location() == state["camera"]
                assert_persistent_viewer()
                state["phase"] = "supersede"
                window.open(str(slow_path), update_texteditor=False)
                state["target"] = window.open(
                    str(replacement_path), update_texteditor=False
                )
            elif state["phase"] == "supersede" and generation == state["target"]:
                assert display.scene_presenter.objects[0] is not state["stable_object"]
                assert display.store_location() == state["camera"]
                assert_persistent_viewer()
                assert_visible_frame()
                state["phase"] = "animation"
                state["target"] = window.open(
                    str(animation_path), update_texteditor=False
                )
            elif state["phase"] == "animation" and generation == state["target"]:
                presenter = display.scene_presenter
                handle = presenter.objects[0].ais_object
                if state["animation_handle"] is None:
                    state["animation_handle"] = handle
                    state["animation_sequence"] = presenter.last_patch_sequence
                if not state["input_sent"]:
                    state["input_sent"] = True
                    display.setFocus()
                    QtTest.QTest.keyPress(display, QtCore.Qt.Key_Right)
                    QtCore.QTimer.singleShot(
                        50,
                        lambda: QtTest.QTest.keyRelease(
                            display, QtCore.Qt.Key_Right
                        ),
                    )
                    return
                if presenter.last_patch_sequence is None:
                    return
                if (
                    state["animation_sequence"] is not None
                    and presenter.last_patch_sequence
                    <= state["animation_sequence"]
                ):
                    return
                assert handle is state["animation_handle"]
                assert display.store_location() == state["camera"]
                assert_persistent_viewer()
                assert_visible_frame()
                state["phase"] = "animation_cancel"
                window._runner_supervisor.cancel_current()
            elif (
                state["phase"] == "animation_cancel"
                and status == "cancelled"
            ):
                assert display.scene_presenter.objects[0].ais_object is state[
                    "animation_handle"
                ]
                assert_persistent_viewer()
                state["phase"] = "done"
                window.close()
                application.quit()

        poll_timer = QtCore.QTimer()
        poll_timer.timeout.connect(poll)
        poll_timer.start(25)

        def fail_timeout():
            if state["phase"] != "done":
                window.close()
                application.exit(2)

        timeout_timer = QtCore.QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(fail_timeout)
        timeout_timer.start(60000)

        window.open(str(script_path))
        exit_code = application.exec()
        assert exit_code == 0, (
            "managed reload smoke timed out in phase {!r}; target status {!r}"
            .format(
                state["phase"],
                window._generation_statuses.get(state["target"]),
            )
        )
        assert state["commits"] == RELOAD_COUNT
        assert state["phase"] == "done"

    print("ZenCad managed reload smoke: OK")


if __name__ == "__main__":
    main()
