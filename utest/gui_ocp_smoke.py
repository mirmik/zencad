#!/usr/bin/env python3
"""Named Linux smoke for the OCP-backed ZenCad viewer."""

from PyQt5 import QtWidgets
from pathlib import Path
from tempfile import TemporaryDirectory


def main():
    application = QtWidgets.QApplication.instance()
    if application is None:
        application = QtWidgets.QApplication([])

    from zencad.gui.display import DisplayWidget
    import zencad
    from zencad.scene import Scene

    scene = Scene()
    interactive = scene.add(zencad.box(10).unlazy())

    widget = DisplayWidget(axis_triedron=False)
    widget.resize(640, 480)
    widget.show()
    application.processEvents()

    assert widget._display._window.IsMapped()
    widget.attach_scene(scene)
    assert widget.Context.IsDisplayed(interactive.ais_object)
    assert interactive.ais_object.Attributes().FaceBoundaryDraw()

    widget.Context.SetSelected(interactive.ais_object, True)
    assert widget.Context.IsSelected(interactive.ais_object)
    widget.Context.ClearSelected(False)
    widget.set_perspective(True)
    widget.set_perspective(False)
    widget.zoom_factor(1.05)
    widget.View.Pan(2, -2)
    widget.redraw()

    with TemporaryDirectory() as temporary_directory:
        image_path = Path(temporary_directory) / "viewer.png"
        assert widget.View.Dump(str(image_path))
        assert image_path.stat().st_size > 0

    widget.close()
    application.processEvents()

    reopened = DisplayWidget(axis_triedron=False)
    reopened.resize(320, 240)
    reopened.show()
    application.processEvents()
    assert reopened._display._window.IsMapped()
    reopened.close()
    application.processEvents()
    print("ZenCad OCP viewer smoke: OK")


if __name__ == "__main__":
    main()
