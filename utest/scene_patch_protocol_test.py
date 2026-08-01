import json
import struct
import unittest
from unittest import mock

import zencad.runtime.scene_patch_protocol as patch_protocol
from zencad.runtime.scene_patch_protocol import (
    MAX_SCENE_PATCH_OBJECT_ID_BYTES,
    SceneObjectPatch,
    ScenePatch,
    ScenePatchCoalescer,
    ScenePatchSequenceError,
    SupersededScenePatchError,
    UnsupportedScenePatchVersion,
    decode_scene_patch_frame,
    encode_scene_patch_frame,
    ensure_current_scene_patch,
)
from zencad.runtime.scene_protocol import ProtocolError


def transform(x=0):
    return {
        "scale": 1,
        "rotation": (0, 0, 0, 1),
        "translation": (x, 2, 3),
    }


class ScenePatchProtocolTest(unittest.TestCase):
    def make_patch(self):
        return ScenePatch(
            generation=7,
            scene_revision=2,
            sequence=11,
            updates=(
                SceneObjectPatch("object-1", {
                    "transform": transform(1),
                    "visible": True,
                    "color": (0.1, 0.2, 0.3, 0.4),
                    "border_color": (0.5, 0.6, 0.7, 0.8),
                    "wire_color": (0.9, 1, 0, 0.1),
                }),
            ),
        )

    def test_round_trip_is_canonical_and_immutable(self):
        source = self.make_patch()
        frame = encode_scene_patch_frame(source)
        restored = decode_scene_patch_frame(frame)

        self.assertEqual(restored, source)
        self.assertEqual(frame, encode_scene_patch_frame(restored))
        self.assertEqual(restored.generation, 7)
        self.assertEqual(restored.scene_revision, 2)
        self.assertEqual(restored.sequence, 11)
        with self.assertRaises(TypeError):
            restored.updates[0].properties["visible"] = False
        with self.assertRaises(TypeError):
            restored.updates[0].properties["transform"]["scale"] = 2

    def test_unknown_version_and_malformed_frames_are_rejected(self):
        frame = bytearray(encode_scene_patch_frame(self.make_patch()))
        struct.pack_into(">H", frame, 4, 99)
        with self.assertRaisesRegex(
            UnsupportedScenePatchVersion, "version 99"
        ):
            decode_scene_patch_frame(bytes(frame))

        valid = encode_scene_patch_frame(self.make_patch())
        for malformed in (valid[:-1], b"no", b"WRNG" + valid[4:]):
            with self.subTest(malformed=malformed[:8]):
                with self.assertRaises(ProtocolError):
                    decode_scene_patch_frame(malformed)

    def test_json_duplicate_property_is_rejected(self):
        payload = (
            b'{"generation":1,"message_type":"scene_patch",'
            b'"protocol_version":1,"scene_revision":0,"sequence":1,'
            b'"updates":[{"object_id":"x","properties":'
            b'{"visible":true,"visible":false}}]}'
        )
        frame = struct.pack(">4sHI", b"ZCPT", 1, len(payload)) + payload
        with self.assertRaisesRegex(ProtocolError, "Duplicate JSON property"):
            decode_scene_patch_frame(frame)

    def test_duplicate_object_updates_are_rejected(self):
        update = SceneObjectPatch("same", {"visible": True})
        with self.assertRaisesRegex(ProtocolError, "IDs must be unique"):
            ScenePatch(1, 0, 1, (update, update))

    def test_property_types_ranges_and_fields_are_strict(self):
        invalid = (
            {"visible": 1},
            {"color": (0, 0, 0, 2)},
            {"color": (0, 0, float("nan"), 0)},
            {"transform": {"scale": 0, "rotation": (0, 0, 0, 1),
                           "translation": (0, 0, 0)}},
            {"transform": {"scale": 1, "rotation": (0, 0, 0, 1),
                           "translation": (0, 0, 0), "extra": 1}},
            {"camera": "fit"},
            {},
        )
        for properties in invalid:
            with self.subTest(properties=properties):
                with self.assertRaises(ProtocolError):
                    SceneObjectPatch("object", properties)

        with self.assertRaises(ProtocolError):
            SceneObjectPatch(
                "x" * (MAX_SCENE_PATCH_OBJECT_ID_BYTES + 1),
                {"visible": True},
            )
        with self.assertRaises(ProtocolError):
            ScenePatch(True, 0, 0)

    def test_unknown_and_missing_wire_fields_are_rejected(self):
        frame = encode_scene_patch_frame(self.make_patch())
        header_size = struct.calcsize(">4sHI")
        message = json.loads(frame[header_size:])
        for mutation in (
            lambda value: value.update(extra=True),
            lambda value: value.pop("sequence"),
            lambda value: value["updates"][0].update(extra=True),
        ):
            changed = json.loads(json.dumps(message))
            mutation(changed)
            payload = json.dumps(changed, separators=(",", ":")).encode()
            changed_frame = struct.pack(">4sHI", b"ZCPT", 1, len(payload)) + payload
            with self.assertRaises(ProtocolError):
                decode_scene_patch_frame(changed_frame)

    def test_size_and_update_count_limits_are_checked(self):
        frame = encode_scene_patch_frame(self.make_patch())
        with mock.patch.object(
            patch_protocol, "MAX_SCENE_PATCH_FRAME_BYTES", len(frame) - 1
        ):
            with self.assertRaisesRegex(ProtocolError, "size limit"):
                encode_scene_patch_frame(self.make_patch())
            with self.assertRaisesRegex(ProtocolError, "size limit"):
                decode_scene_patch_frame(frame)

        with mock.patch.object(patch_protocol, "MAX_SCENE_PATCH_UPDATES", 1):
            with self.assertRaisesRegex(ProtocolError, "count"):
                ScenePatch(1, 0, 1, (
                    SceneObjectPatch("one", {"visible": True}),
                    SceneObjectPatch("two", {"visible": True}),
                ))

    def test_current_scene_check_happens_on_generation_and_revision(self):
        patch = self.make_patch()
        ensure_current_scene_patch(patch, 7, 2)
        for current in ((8, 2), (7, 3)):
            with self.subTest(current=current):
                with self.assertRaises(SupersededScenePatchError):
                    ensure_current_scene_patch(patch, *current)

    def test_coalescer_merges_absolute_latest_state_and_allows_gaps(self):
        coalescer = ScenePatchCoalescer(max_objects=2)
        coalescer.push(ScenePatch(4, 3, 10, (
            SceneObjectPatch("one", {
                "visible": True,
                "transform": transform(1),
            }),
        )))
        coalescer.push(ScenePatch(4, 3, 15, (
            SceneObjectPatch("one", {
                "visible": False,
                "color": (1, 0, 0, 0.5),
            }),
            SceneObjectPatch("two", {"wire_color": (0, 1, 0, 0)}),
        )))

        merged = coalescer.drain()
        self.assertEqual(merged.sequence, 15)
        self.assertEqual([u.object_id for u in merged.updates], ["one", "two"])
        first = merged.updates[0].properties
        self.assertFalse(first["visible"])
        self.assertEqual(first["transform"]["translation"], (1.0, 2.0, 3.0))
        self.assertEqual(first["color"], (1.0, 0.0, 0.0, 0.5))
        self.assertIsNone(coalescer.drain())

        coalescer.push(ScenePatch(4, 3, 20, (
            SceneObjectPatch("one", {"visible": True}),
        )))
        self.assertEqual(coalescer.drain().sequence, 20)

    def test_coalescer_is_bounded_and_rejects_mixed_or_reordered_streams(self):
        coalescer = ScenePatchCoalescer(max_objects=1)
        coalescer.push(ScenePatch(1, 0, 2, (
            SceneObjectPatch("one", {"visible": True}),
        )))
        with self.assertRaisesRegex(ProtocolError, "object limit"):
            coalescer.push(ScenePatch(1, 0, 3, (
                SceneObjectPatch("two", {"visible": True}),
            )))
        with self.assertRaises(ScenePatchSequenceError):
            coalescer.push(ScenePatch(1, 0, 2, ()))
        with self.assertRaises(SupersededScenePatchError):
            coalescer.push(ScenePatch(2, 0, 4, ()))

        coalescer.clear()
        coalescer.push(ScenePatch(2, 1, 0, (
            SceneObjectPatch("new", {"visible": False}),
        )))
        self.assertEqual(coalescer.drain().generation, 2)


if __name__ == "__main__":
    unittest.main()
