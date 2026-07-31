#!/usr/bin/env python3
"""Named GUI smoke for managed reload into one persistent viewer."""

from pathlib import Path
from tempfile import TemporaryDirectory

RELOAD_COUNT = 20


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtWidgets

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from zencad.gui.mainwindow import MainWindow

    with TemporaryDirectory() as temporary_directory:
        script_path = Path(temporary_directory) / "model.py"
        script_path.write_text(
            "from zencad import *\n"
            "print('managed reload')\n"
            "display(box(10))\n"
            "show()\n",
            encoding="utf-8",
        )
        error_path = Path(temporary_directory) / "error.py"
        error_path.write_text(
            "raise RuntimeError('expected reload failure')\n",
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

        window = MainWindow(restore_gui=False, managed_runtime=True)
        display = window.display_widget
        window.resize(800, 600)
        window.show()
        application.processEvents()

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
        }

        def assert_persistent_viewer():
            assert int(display.winId()) == native_window
            assert display.Viewer is viewer
            assert display.View is view
            assert display.Context is context
            assert window.texteditor is editor
            assert window.console is console

        def assert_visible_frame():
            display.redraw()
            application.processEvents()
            image = application.primaryScreen().grabWindow(
                int(display.winId())
            ).toImage()
            colors = {
                image.pixelColor(x, y).rgb()
                for x in range(0, image.width(), max(1, image.width() // 16))
                for y in range(0, image.height(), max(1, image.height() // 16))
            }
            assert len(colors) > 4, "viewer framebuffer is blank"

        def start_cancel_case():
            state["phase"] = "cancel"
            state["target"] = window.open(
                str(slow_path), update_texteditor=False
            )
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
                assert display.scene_presenter.objects
                assert_persistent_viewer()

                if state["commits"] == 1:
                    display.set_scale(3.5)
                    state["camera"] = display.store_location()
                else:
                    assert display.store_location() == state["camera"]

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
        assert exit_code == 0, "managed reload smoke timed out"
        assert state["commits"] == RELOAD_COUNT
        assert state["phase"] == "done"

    print("ZenCad managed reload smoke: OK")


if __name__ == "__main__":
    main()
