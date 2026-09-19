#!/usr/bin/env python3
"""Named GUI smoke for managed reload into one persistent viewer."""

from pathlib import Path
import math
import sys
from tempfile import TemporaryDirectory
from unittest import mock

RELOAD_COUNT = 20


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from zencad.gui.mainwindow import MainWindow
    from zencad.gui.settingswdg import SettingsWidget
    from zencad.settings import Settings

    with TemporaryDirectory() as temporary_directory:
        script_path = Path(temporary_directory) / "model.py"
        script_path.write_text(
            "from zencad import *\n"
            "from zencad.interactive import arrow\n"
            "print('managed reload')\n"
            "display(box(10))\n"
            "display(box(6).right(20).to_mesh(), color=color.yellow)\n"
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
            "display(sphere(70).translate(1000, -2000, 3000))\n"
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
        bundled_example = (
            Path(__file__).parents[1]
            / "zencad/examples/0.Base/helloworld.py"
        )
        bundled_contents = bundled_example.read_text(encoding="utf-8")
        recent_before = list(Settings.get(["memory", "recents"]) or [])
        example_action = next(
            action
            for action in window.findChildren(QtWidgets.QAction)
            if action.text() == "helloworld.py"
            and "editable temporary copy" in action.statusTip()
        )
        example_action.trigger()
        example_copy = Path(window.current_opened())
        assert example_copy != bundled_example
        assert example_copy.read_text(encoding="utf-8") == bundled_contents
        assert window.current_opened() == str(example_copy)
        assert "editable example copy" in window.windowTitle()
        assert list(Settings.get(["memory", "recents"]) or []) == recent_before
        window.texteditor.appendPlainText("# edited copy")
        window.saveAction()
        assert bundled_example.read_text(encoding="utf-8") == bundled_contents
        assert example_copy.read_text(encoding="utf-8").rstrip().endswith(
            "# edited copy"
        )
        state_example_copy = example_copy
        saved_example = Path(temporary_directory) / "saved-example.py"
        with mock.patch(
            "zencad.gui.actions.QFileDialog.getSaveFileName",
            return_value=(str(saved_example), "*.py"),
        ):
            window.saveAsAction()
        assert window.current_opened() == str(saved_example)
        assert window.windowTitle() == str(saved_example)
        assert saved_example.read_text(encoding="utf-8").rstrip().endswith(
            "# edited copy"
        )
        assert Settings.get(["memory", "recents"])[0] == str(saved_example)
        application.processEvents()
        example_generation = window._runner_supervisor.current_generation
        window._runner_supervisor.cancel_current()
        window._runner_supervisor.wait(example_generation, timeout=10)
        for _attempt in range(10):
            application.processEvents()
            if not window.calculation_overlay.active:
                break
            QtTest.QTest.qWait(10)
        with mock.patch(
            "zencad.gui.actions.QMessageBox.about"
        ) as about_dialog:
            window.aboutAction()
        about_html = about_dialog.call_args.args[2]
        assert "ZenCad version: 2.0.0" in about_html
        assert "2018-2021, 2026" in about_html
        settings_dialog = SettingsWidget()
        navigation_combo = settings_dialog.navigation_scheme_edit.combo
        for scheme in (
            "zencad",
            "classic",
            "blender",
            "freecad",
            "maya",
            "custom",
        ):
            assert navigation_combo.findData(scheme) >= 0
        navigation_combo.setCurrentIndex(navigation_combo.findData("custom"))
        assert settings_dialog.navigation_rotate_edit.isEnabled()
        assert settings_dialog.navigation_pan_edit.isEnabled()
        settings_dialog.navigation_rotate_edit.combo.setCurrentIndex(
            settings_dialog.navigation_rotate_edit.combo.findData("middle")
        )
        settings_dialog.navigation_pan_edit.combo.setCurrentIndex(
            settings_dialog.navigation_pan_edit.combo.findData("middle")
        )
        with mock.patch(
            "zencad.gui.settingswdg.QMessageBox.warning"
        ) as navigation_warning:
            assert not settings_dialog.navigation_settings_are_valid()
        navigation_warning.assert_called_once()
        settings_dialog.close()
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

        def assert_default_camera(center):
            from zencad.gui.display import STARTED_YAW, STARTED_PITCH

            direction = display.View.Camera().Direction().Coord()
            expected = (
                math.cos(STARTED_PITCH) * math.cos(STARTED_YAW),
                math.cos(STARTED_PITCH) * math.sin(STARTED_YAW),
                math.sin(STARTED_PITCH),
            )
            assert all(abs(a - b) < 1e-7 for a, b in zip(direction, expected))
            actual_center = display.store_location()["center"]
            # AIS bounds can follow tessellation rather than exact extrema.
            assert all(abs(a - b) < 0.1 for a, b in zip(actual_center, center)), actual_center

        def change_camera():
            display.yaw = 0.3
            display.pitch = -0.2
            display.set_orient1()
            display.set_scale(20.0)
            state["camera"] = display.store_location()

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
                assert len(display.scene_presenter.objects) == 4
                assert [
                    type(item.ais_object).__name__
                    for item in display.scene_presenter.objects
                ] == [
                    "AIS_Shape",
                    "AIS_Triangulation",
                    "AIS_Point",
                    "AIS_Line",
                ]
                assert (
                    display.scene_presenter.objects[1]
                    .ais_object.DisplayMode()
                    == 0
                )
                assert (
                    display.scene_presenter.objects[1]
                    .ais_object.Attributes()
                    .ShadingAspect().Aspect().ToDrawEdges()
                )
                assert_persistent_viewer()

                if state["commits"] == 1:
                    display.set_navigation_scheme("zencad")
                    camera_before_pan = display.store_location()
                    start = QtCore.QPointF(150, 150)
                    finish = QtCore.QPointF(190, 170)
                    application.sendEvent(display, QtGui.QMouseEvent(
                        QtCore.QEvent.MouseButtonPress,
                        start,
                        QtCore.Qt.MiddleButton,
                        QtCore.Qt.MiddleButton,
                        QtCore.Qt.NoModifier,
                    ))
                    application.sendEvent(display, QtGui.QMouseEvent(
                        QtCore.QEvent.MouseMove,
                        finish,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.MiddleButton,
                        QtCore.Qt.NoModifier,
                    ))
                    application.sendEvent(display, QtGui.QMouseEvent(
                        QtCore.QEvent.MouseButtonRelease,
                        finish,
                        QtCore.Qt.MiddleButton,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoModifier,
                    ))
                    camera_after_pan = display.store_location()
                    assert camera_after_pan["center"] != camera_before_pan["center"]
                    assert camera_after_pan["scale"] == camera_before_pan["scale"]
                    # Keep a deliberately non-default camera while leaving
                    # enough of the model visible in the full-size viewport.
                    change_camera()
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
                # The same filename must still reset after its failed first run.
                window.notifier.clear()
                error_path.write_text(replacement_path.read_text(), encoding="utf-8")
                state["phase"] = "retry"
                state["target"] = window.open(str(error_path), update_texteditor=False)
            elif state["phase"] == "retry" and generation == state["target"]:
                assert_default_camera((1000, -2000, 3000))
                assert 100 < display.scale() < 500
                state["generation"] = generation
                state["stable_object"] = display.scene_presenter.objects[0]
                change_camera()
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
                assert_default_camera((1000, -2000, 3000))
                assert 100 < display.scale() < 500
                assert_persistent_viewer()
                assert_visible_frame()
                change_camera()
                state["phase"] = "animation"
                state["target"] = window.open(
                    str(animation_path), update_texteditor=False
                )
            elif state["phase"] == "animation" and generation == state["target"]:
                presenter = display.scene_presenter
                handle = presenter.objects[0].ais_object
                if state["animation_handle"] is None:
                    assert_default_camera((0, 0, 0))
                    assert display.store_location() != state["camera"]
                    state["camera"] = display.store_location()
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
        assert not state_example_copy.exists()

    print("ZenCad managed reload smoke: OK")


if __name__ == "__main__":
    main()
