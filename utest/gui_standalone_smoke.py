#!/usr/bin/env python3
"""Exercise direct show() in one process without foreign window embedding."""

from pathlib import Path
from tempfile import TemporaryDirectory


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtGui, QtWidgets
    from OCP.AIS import AIS_Triangulation
    from zencad import display, show, torus, translate

    controller = display(torus(20, 6).to_mesh())
    assert isinstance(controller.ais_object, AIS_Triangulation)
    assert controller.ais_object.DisplayMode() == 0
    state = {"updates": 0, "closed": False, "window": None}
    frame_directory = TemporaryDirectory()

    def animate(animation_state):
        state["updates"] += 1
        controller.relocate(translate(state["updates"], 0, 0))

    def preanimate(widget, animation_thread):
        application = QtWidgets.QApplication.instance()
        assert application is not None
        assert widget.parent() is None
        state["window"] = int(widget.winId())

        def verify_frame():
            frame = Path(frame_directory.name) / "mesh.png"
            widget.redraw()
            assert widget.View.Dump(str(frame))
            image = QtGui.QImage(str(frame))
            assert not image.isNull()
            colored_samples = 0
            for x in range(0, image.width(), max(1, image.width() // 32)):
                for y in range(0, image.height(), max(1, image.height() // 32)):
                    pixel = image.pixelColor(x, y)
                    channels = (pixel.red(), pixel.green(), pixel.blue())
                    if max(channels) - min(channels) > 30:
                        colored_samples += 1
            assert colored_samples > 20, colored_samples
            widget.close()

        QtCore.QTimer.singleShot(500, verify_frame)

    def close_handle():
        state["closed"] = True
        assert state["updates"] > 0
        print("ZenCad same-process standalone smoke: OK")

    show(
        animate=animate,
        preanimate=preanimate,
        close_handle=close_handle,
        animate_step=0.01,
    )
    frame_directory.cleanup()


if __name__ == "__main__":
    main()
