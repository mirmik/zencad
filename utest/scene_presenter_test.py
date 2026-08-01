import unittest

import zencad
from zencad.gui.scene_presenter import (
    PresentedSceneObject,
    ScenePresentationError,
    ScenePresenter,
    materialize_scene_object,
)
from zencad.runtime.scene_protocol import SceneObjectRecord, SceneSnapshot, encode_brep
from zencad.runtime.scene_patch_protocol import SceneObjectPatch, ScenePatch


class FakeHandle:
    def __init__(self, object_id):
        self.object_id = object_id
        self.state = None
        self.fail_next_patch = False


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

    def Erase(self, handle, update):
        self.calls.append(("erase", handle.object_id, update))
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


def fake_patch_applier(item, old_state, new_state, changed):
    item.ais_object.state = dict(new_state)
    if item.ais_object.fail_next_patch:
        item.ais_object.fail_next_patch = False
        raise RuntimeError("patch failed")


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

    def test_real_materializer_creates_styled_detached_ais_shape(self):
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

    def test_patch_updates_existing_handles_once_and_tracks_sequence(self):
        widget = FakeWidget()
        presenter = ScenePresenter(
            widget,
            materializer=fake_materializer,
            patch_applier=fake_patch_applier,
        )
        presenter.apply(snapshot(4, record("one"), record("two")))
        first_handle = presenter.objects[0].ais_object
        updates_before = widget.Context.update_count

        sequence = presenter.apply_patch(ScenePatch(4, 0, 3, (
            SceneObjectPatch("one", {
                "visible": False,
                "color": (1, 0, 0, 0.25),
                "transform": {
                    "scale": 1,
                    "rotation": (0, 0, 0, 1),
                    "translation": (5, 6, 7),
                },
            }),
            SceneObjectPatch("two", {
                "border_color": (0, 1, 0, 0),
                "wire_color": (0, 0, 1, 0),
            }),
        )))

        self.assertEqual(sequence, 3)
        self.assertEqual(presenter.last_patch_sequence, 3)
        self.assertIs(presenter.objects[0].ais_object, first_handle)
        self.assertFalse(presenter.objects[0].visible)
        self.assertEqual(
            presenter.objects[0].properties["transform"]["translation"],
            (5.0, 6.0, 7.0),
        )
        self.assertNotIn(first_handle, widget.Context.active)
        self.assertEqual(widget.Context.update_count, updates_before + 1)
        self.assertEqual(widget.thread_checks, 2)

    def test_stale_reordered_and_unknown_patches_do_not_mutate_scene(self):
        widget = FakeWidget()
        presenter = ScenePresenter(
            widget,
            materializer=fake_materializer,
            patch_applier=fake_patch_applier,
        )
        presenter.apply(snapshot(5, record("one")), scene_revision=2)
        presenter.apply_patch(ScenePatch(5, 2, 10, (
            SceneObjectPatch("one", {"visible": False}),
        )))
        state = presenter.objects[0].properties
        updates = widget.Context.update_count

        invalid = (
            ScenePatch(6, 2, 11, (
                SceneObjectPatch("one", {"visible": True}),
            )),
            ScenePatch(5, 3, 11, (
                SceneObjectPatch("one", {"visible": True}),
            )),
            ScenePatch(5, 2, 10, (
                SceneObjectPatch("one", {"visible": True}),
            )),
            ScenePatch(5, 2, 11, (
                SceneObjectPatch("missing", {"visible": True}),
            )),
        )
        for patch in invalid:
            with self.subTest(patch=patch):
                with self.assertRaises(Exception):
                    presenter.apply_patch(patch)
                self.assertEqual(presenter.objects[0].properties, state)
                self.assertEqual(widget.Context.update_count, updates)

    def test_patch_failure_rolls_back_all_touched_objects(self):
        widget = FakeWidget()
        presenter = ScenePresenter(
            widget,
            materializer=fake_materializer,
            patch_applier=fake_patch_applier,
        )
        presenter.apply(snapshot(8, record("one"), record("two")))
        old_states = tuple(item.properties for item in presenter.objects)
        presenter.objects[1].ais_object.fail_next_patch = True
        updates_before = widget.Context.update_count

        with self.assertRaisesRegex(ScenePresentationError, "commit"):
            presenter.apply_patch(ScenePatch(8, 0, 1, (
                SceneObjectPatch("one", {"color": (1, 0, 0, 0)}),
                SceneObjectPatch("two", {"visible": False}),
            )))

        self.assertEqual(
            tuple(item.properties for item in presenter.objects),
            old_states,
        )
        self.assertTrue(all(
            item.ais_object in widget.Context.active
            for item in presenter.objects
        ))
        self.assertIsNone(presenter.last_patch_sequence)
        self.assertEqual(widget.Context.update_count, updates_before + 1)


if __name__ == "__main__":
    unittest.main()
