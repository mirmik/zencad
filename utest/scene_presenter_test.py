import unittest

import zencad
from zencad.gui.scene_presenter import (
    PresentedSceneObject,
    ScenePresentationError,
    ScenePresenter,
    materialize_scene_object,
)
from zencad.runtime.scene_protocol import SceneObjectRecord, SceneSnapshot, encode_brep


class FakeHandle:
    def __init__(self, object_id):
        self.object_id = object_id


class FakeContext:
    def __init__(self):
        self.active = []
        self.calls = []
        self.update_count = 0
        self.selection_clear_count = 0
        self.fail_display_id = None

    def Display(self, handle, update):
        self.calls.append(("display", handle.object_id, update))
        if handle.object_id == self.fail_display_id:
            raise RuntimeError("display failed")
        if handle not in self.active:
            self.active.append(handle)

    def Remove(self, handle, update):
        self.calls.append(("remove", handle.object_id, update))
        if handle in self.active:
            self.active.remove(handle)

    def ClearSelected(self, update):
        self.calls.append(("clear-selection", update))
        self.selection_clear_count += 1

    def UpdateCurrentViewer(self):
        self.calls.append(("update",))
        self.update_count += 1


class FakeView:
    def __init__(self):
        self.fit_calls = []

    def FitAll(self, margin, update):
        self.fit_calls.append((margin, update))


class FakeWidget:
    def __init__(self):
        self.Context = FakeContext()
        self.View = FakeView()
        self.camera = {
            "scale": 2.0,
            "eye": (1.0, 2.0, 3.0),
            "center": (0.0, 0.0, 0.0),
        }
        self.thread_checks = 0

    def assert_gui_thread(self):
        self.thread_checks += 1

    def store_location(self):
        return dict(self.camera)

    def restore_location(self, camera, redraw=True):
        if redraw:
            raise AssertionError("transactional camera changes must not redraw")
        self.camera = dict(camera)


def record(object_id, kind="brep", visible=True):
    return SceneObjectRecord(
        object_id=object_id,
        kind=kind,
        payload=b"fake",
        properties={"visible": visible},
    )


def snapshot(generation, *records, camera_policy="preserve", metadata=None):
    return SceneSnapshot(
        generation=generation,
        objects=tuple(records),
        camera_policy=camera_policy,
        metadata=metadata or {},
    )


def fake_materializer(item):
    if item.kind != "brep":
        raise ScenePresentationError(f"unsupported {item.kind}")
    return PresentedSceneObject(
        object_id=item.object_id,
        ais_object=FakeHandle(item.object_id),
        shape=item.object_id,
        visible=item.properties.get("visible", True),
    )


class ScenePresenterTest(unittest.TestCase):
    def test_two_snapshots_reuse_viewer_and_update_once_each(self):
        widget = FakeWidget()
        permanent = FakeHandle("permanent-axis")
        widget.Context.active.append(permanent)
        context_identity = id(widget.Context)
        view_identity = id(widget.View)
        presenter = ScenePresenter(widget, materializer=fake_materializer)

        presenter.apply(snapshot(1, record("one")))
        self.assertEqual(widget.View.fit_calls, [(0.07, False)])
        presenter.apply(snapshot(2, record("two")))

        self.assertEqual(id(widget.Context), context_identity)
        self.assertEqual(id(widget.View), view_identity)
        self.assertIn(permanent, widget.Context.active)
        self.assertEqual(
            [item.object_id for item in widget.Context.active],
            ["permanent-axis", "two"],
        )
        self.assertEqual(widget.Context.update_count, 2)
        self.assertEqual(widget.Context.selection_clear_count, 2)
        self.assertEqual(widget.thread_checks, 2)
        self.assertEqual(widget.View.fit_calls, [(0.07, False)])
        self.assertFalse(any(call[-1] is True for call in widget.Context.calls))

    def test_invalid_snapshot_preserves_scene_camera_and_selection(self):
        widget = FakeWidget()
        presenter = ScenePresenter(widget, materializer=fake_materializer)
        presenter.apply(snapshot(1, record("good")))
        old_objects = tuple(widget.Context.active)
        old_camera = dict(widget.camera)
        old_updates = widget.Context.update_count
        old_selection_clears = widget.Context.selection_clear_count

        with self.assertRaises(ScenePresentationError):
            presenter.apply(snapshot(2, record("bad", kind="unsupported")))

        self.assertEqual(tuple(widget.Context.active), old_objects)
        self.assertEqual(widget.camera, old_camera)
        self.assertEqual(widget.Context.update_count, old_updates)
        self.assertEqual(
            widget.Context.selection_clear_count,
            old_selection_clears,
        )
        self.assertEqual(presenter.committed_generation, 1)

    def test_commit_failure_rolls_back_previous_scene_and_camera(self):
        widget = FakeWidget()
        presenter = ScenePresenter(widget, materializer=fake_materializer)
        presenter.apply(snapshot(1, record("old")))
        old_camera = dict(widget.camera)
        old_selection_clears = widget.Context.selection_clear_count
        widget.Context.fail_display_id = "new"

        with self.assertRaisesRegex(ScenePresentationError, "commit"):
            presenter.apply(snapshot(2, record("new")))

        self.assertEqual(
            [item.object_id for item in widget.Context.active],
            ["old"],
        )
        self.assertEqual(widget.camera, old_camera)
        self.assertEqual(
            widget.Context.selection_clear_count,
            old_selection_clears,
        )
        self.assertEqual(presenter.committed_generation, 1)

    def test_fit_and_explicit_camera_policies(self):
        widget = FakeWidget()
        presenter = ScenePresenter(widget, materializer=fake_materializer)
        presenter.apply(snapshot(1, record("one"), camera_policy="fit"))
        presenter.apply(snapshot(
            2,
            record("two"),
            camera_policy="explicit",
            metadata={
                "camera": {
                    "scale": 9,
                    "eye": (8, 7, 6),
                    "center": (3, 2, 1),
                },
            },
        ))

        self.assertEqual(widget.View.fit_calls, [(0.07, False)])
        self.assertEqual(widget.camera, {
            "scale": 9.0,
            "eye": (8.0, 7.0, 6.0),
            "center": (3.0, 2.0, 1.0),
        })

    def test_real_materializer_creates_styled_unbound_ais_shape(self):
        source = SceneObjectRecord(
            object_id="box",
            kind="brep",
            payload=encode_brep(zencad.box(1).unlazy()),
            properties={
                "visible": False,
                "color": (0.1, 0.2, 0.3, 0.4),
                "border_color": (0.5, 0.6, 0.7, 0),
                "wire_color": (0.8, 0.9, 1.0, 0),
                "transform": {
                    "scale": 1,
                    "rotation": (0, 0, 0, 1),
                    "translation": (4, 5, 6),
                },
            },
        )
        presented = materialize_scene_object(source)
        translation = presented.ais_object.LocalTransformation().TranslationPart()

        self.assertEqual(presented.object_id, "box")
        self.assertFalse(presented.visible)
        self.assertAlmostEqual(translation.X(), 4)
        self.assertAlmostEqual(translation.Y(), 5)
        self.assertAlmostEqual(translation.Z(), 6)


if __name__ == "__main__":
    unittest.main()
