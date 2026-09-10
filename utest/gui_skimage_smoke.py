#!/usr/bin/env python3
"""Open the raster-contour cube and wait for a displayed animation frame.

Requires the gui and examples extras; on Linux run with xvfb-run -a.
The parent process bounds execution even if OCCT blocks the Qt event loop.
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if "--viewer" not in sys.argv:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
        subprocess.run(
            [sys.executable, __file__, "--viewer"],
            env=environment, check=True, timeout=60,
        )
        print("ZenCad skimage cube viewer smoke: OK")
        return

    from tempfile import TemporaryDirectory
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()
    from PyQt5 import QtCore, QtWidgets
    from OCP.BRepCheck import BRepCheck_Analyzer
    from zencad.gui.mainwindow import MainWindow

    application = QtWidgets.QApplication([])
    with TemporaryDirectory() as cache:
        window = MainWindow(restore_gui=False)
        window._runner_supervisor.cache_directory = Path(cache)
        window._runner_supervisor.cache_enabled = True
        window.show()
        application.processEvents()
        example = ROOT / "zencad/examples/Integration/skimage-mechanicus/cube.py"
        generation = window.open(str(example))
        passed = False

        def poll():
            nonlocal passed
            presenter = window.display_widget.scene_presenter
            if presenter.committed_generation != generation:
                return
            if presenter.last_patch_sequence is None:
                return
            assert len(presenter.objects) == 13
            # Identical copies need only one validity check per geometry.
            for index in (0, 6, 12):
                assert BRepCheck_Analyzer(presenter.objects[index].shape).IsValid()
            image = Path(cache) / "frame.png"
            assert window.display_widget.View.Dump(str(image))
            assert image.stat().st_size > 0
            passed = True
            window.close()
            application.quit()

        timer = QtCore.QTimer()
        timer.timeout.connect(poll)
        timer.start(100)
        try:
            application.exec()
            assert passed, "cube did not reach a displayed animation frame"
        finally:
            window.close()


if __name__ == "__main__":
    main()
