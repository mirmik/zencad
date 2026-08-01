#!/usr/bin/env python3
"""Drive managed Tetris through InputEvent in one persistent viewer."""

from pathlib import Path


ROOT = Path(__file__).parents[1]


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtTest, QtWidgets

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from zencad.gui.mainwindow import MainWindow

    window = MainWindow(restore_gui=False, managed_runtime=True)
    display = window.display_widget
    window.resize(800, 600)
    window.show()
    application.processEvents()

    native_window = int(display.winId())
    view = display.View
    context = display.Context
    target = window.open(
        str(ROOT / "zencad/examples/MiniGames/tetris.py"),
        update_texteditor=False,
    )
    state = {
        "phase": "load",
        "sequence": None,
        "handles": None,
        "responsive_ticks": 0,
    }

    responsiveness_timer = QtCore.QTimer()
    responsiveness_timer.timeout.connect(
        lambda: state.__setitem__(
            "responsive_ticks", state["responsive_ticks"] + 1
        )
    )
    responsiveness_timer.start(10)

    def poll():
        presenter = display.scene_presenter
        if presenter.committed_generation != target:
            return
        if state["phase"] == "load":
            if presenter.last_patch_sequence is None:
                return
            state["sequence"] = presenter.last_patch_sequence
            state["handles"] = tuple(item.ais_object for item in presenter.objects)
            state["phase"] = "input"
            display.setFocus()
            QtTest.QTest.keyClick(display, QtCore.Qt.Key_Right)
            return
        if state["phase"] == "input":
            if presenter.last_patch_sequence <= state["sequence"]:
                return
            assert tuple(
                item.ais_object for item in presenter.objects
            ) == state["handles"]
            assert int(display.winId()) == native_window
            assert display.View is view
            assert display.Context is context
            assert state["responsive_ticks"] > 5
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
    assert exit_code == 0, f"managed games smoke stalled in {state['phase']}"
    assert state["phase"] == "done"
    print("ZenCad managed games smoke: OK")


if __name__ == "__main__":
    main()
