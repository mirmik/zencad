#!/usr/bin/env python3
"""Named Linux smoke for the OCP-backed ZenCad viewer."""

from zencad.gui.qt_backend import configure_qt_platform

configure_qt_platform()

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
    interactive = scene.add(zencad.box(10))

    widget = DisplayWidget(axis_triedron=False)
    widget.resize(640, 480)
    widget.show()
    application.processEvents()

    assert widget._display._window.IsMapped()
    assert widget.msaa_samples in (0, 2, 4, 8)
    assert (
        widget.View.RenderingParams().NbMsaaSamples
        == widget.msaa_samples
    )
    widget.set_msaa_samples(2)
    assert widget.View.RenderingParams().NbMsaaSamples == 2
    widget.set_msaa_samples(4)
    assert widget.View.RenderingParams().NbMsaaSamples == 4
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
    assert widget._display._closed
    assert widget.close_viewer() is False

    reopened = DisplayWidget(axis_triedron=False)
    reopened.resize(320, 240)
    reopened.show()
    application.processEvents()
    assert reopened._display._window.IsMapped()

    from zencad.gui.scene_presenter import ScenePresentationError
    from zencad.runtime.scene_protocol import SceneObjectRecord, SceneSnapshot
    from zencad.scene_draft import SceneDraft

    window_id = int(reopened.winId())
    viewer = reopened.Viewer
    view = reopened.View
    context = reopened.Context

    first_draft = SceneDraft(1)
    first_draft.add(zencad.box(5))
    reopened.apply_snapshot(first_draft.snapshot())
    first_object = reopened.scene_presenter.objects[0].ais_object
    assert context.IsDisplayed(first_object)
    reopened.set_scale(3.5)
    camera = reopened.store_location()
    context.SetSelected(first_object, True)

    second_draft = SceneDraft(2)
    second_draft.add(zencad.sphere(3))
    reopened.apply_snapshot(second_draft.snapshot())
    second_object = reopened.scene_presenter.objects[0].ais_object
    assert not context.IsDisplayed(first_object)
    assert context.IsDisplayed(second_object)
    assert context.NbSelected() == 0
    assert reopened.store_location() == camera
    assert int(reopened.winId()) == window_id
    assert reopened.Viewer is viewer
    assert reopened.View is view
    assert reopened.Context is context

    invalid = SceneSnapshot(
        generation=3,
        objects=(SceneObjectRecord("bad", "unsupported", b"bad"),),
    )
    try:
        reopened.apply_snapshot(invalid)
    except ScenePresentationError:
        pass
    else:
        raise AssertionError("invalid snapshot was accepted")
    assert context.IsDisplayed(second_object)
    assert reopened.store_location() == camera

    reopened.close()
    application.processEvents()
    assert reopened._display._closed
    assert reopened.close_viewer() is False
    print("ZenCad OCP viewer smoke: OK")


if __name__ == "__main__":
    main()
