#!/usr/bin/env python3
"""Exercise managed CameraAction against a real persistent OCCT viewer."""

import math
from pathlib import Path


ROOT = Path(__file__).parents[1]


def point_tuple(point):
    return point.X(), point.Y(), point.Z()


def distance(left, right):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def close_point(left, right, tolerance=1e-9):
    return distance(left, right) <= tolerance


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from OCP.gp import gp_Pnt
    from PyQt5 import QtCore, QtWidgets
    from zencad.gui.mainwindow import MainWindow

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = MainWindow(restore_gui=False)
    display = window.display_widget
    window.resize(800, 600)
    window.show()
    application.processEvents()

    native_window = int(display.winId())
    view = display.View
    context = display.Context
    target = window.open(
        str(ROOT / "zencad/examples/3.Animation/camera.py"),
        update_texteditor=False,
    )
    state = {
        "phase": "load",
        "sequence": None,
        "eye": None,
        "center": None,
        "scale": None,
        "projection": None,
        "handle": None,
        "manual_z": None,
    }

    def poll():
        presenter = display.scene_presenter
        camera_presenter = display.camera_action_presenter
        if presenter.committed_generation != target:
            return
        if state["phase"] == "load":
            if camera_presenter.last_sequence is None:
                return
            camera = display.View.Camera()
            state.update({
                "phase": "orbit",
                "sequence": camera_presenter.last_sequence,
                "eye": point_tuple(camera.Eye()),
                "center": point_tuple(camera.Center()),
                "scale": camera.Scale(),
                "projection": camera.ProjectionType(),
                "handle": presenter.objects[0].ais_object,
            })
            return
        if state["phase"] == "orbit":
            if camera_presenter.last_sequence < state["sequence"] + 5:
                return
            camera = display.View.Camera()
            assert distance(point_tuple(camera.Eye()), state["eye"]) > 1e-6
            assert close_point(point_tuple(camera.Center()), state["center"])
            assert camera.Scale() == state["scale"]
            assert camera.ProjectionType() == state["projection"]
            assert presenter.objects[0].ais_object is state["handle"]
            assert presenter.objects[0].properties["transform"]["rotation"] == (
                0.0, 0.0, 0.0, 1.0
            )
            center = camera.Center()
            state["manual_z"] = center.Z() + 7.0
            camera.SetEye(gp_Pnt(center.X() + 20.0, center.Y(), state["manual_z"]))
            display.update_orient1_from_view()
            state["sequence"] = camera_presenter.last_sequence
            state["phase"] = "manual-base"
            return
        if state["phase"] == "manual-base":
            if camera_presenter.last_sequence < state["sequence"] + 3:
                return
            camera = display.View.Camera()
            assert abs(camera.Eye().Z() - state["manual_z"]) < 1e-8
            assert close_point(point_tuple(camera.Center()), state["center"])
            assert camera.Scale() == state["scale"]
            assert int(display.winId()) == native_window
            assert display.View is view
            assert display.Context is context
            state["phase"] = "cancel"
            window._runner_supervisor.cancel_current()
            return
        if (
            state["phase"] == "cancel"
            and window._generation_statuses.get(target) == "cancelled"
        ):
            state["phase"] = "done"
            window.close()
            application.quit()

    poll_timer = QtCore.QTimer()
    poll_timer.timeout.connect(poll)
    poll_timer.start(10)

    def fail_timeout():
        if state["phase"] != "done":
            window.close()
            application.exit(2)

    timeout_timer = QtCore.QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(fail_timeout)
    timeout_timer.start(45000)

    exit_code = application.exec()
    assert exit_code == 0, f"managed camera smoke stalled in {state['phase']}"
    assert state["phase"] == "done"
    print("ZenCad managed camera smoke: OK")


if __name__ == "__main__":
    main()
