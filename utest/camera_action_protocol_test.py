import json
import math
import struct
import unittest

from zencad.runtime.camera_action_protocol import (
    CameraAction,
    CameraActionCoalescer,
    CameraActionSequenceError,
    SupersededCameraActionError,
    UnsupportedCameraActionVersion,
    decode_camera_action_frame,
    encode_camera_action_frame,
    ensure_current_camera_action,
    quaternion_from_axis_angle,
    quaternion_multiply,
    relative_quaternion,
    rotate_vector,
)
from zencad.runtime.scene_protocol import ProtocolError


def assert_vector_close(test, actual, expected):
    for got, wanted in zip(actual, expected):
        test.assertAlmostEqual(got, wanted, places=10)


class CameraActionProtocolTest(unittest.TestCase):
    def make_action(self):
        return CameraAction(
            generation=7,
            scene_revision=2,
            sequence=11,
            action_revision=15,
            cumulative_orbit=quaternion_from_axis_angle((0, 0, 1), 0.5),
        )

    def test_round_trip_is_canonical_and_sign_stable(self):
        action = self.make_action()
        frame = encode_camera_action_frame(action)
        restored = decode_camera_action_frame(frame)

        self.assertEqual(restored, action)
        self.assertEqual(encode_camera_action_frame(restored), frame)
        negative = tuple(-value for value in action.cumulative_orbit)
        self.assertEqual(
            CameraAction(7, 2, 11, 15, negative).cumulative_orbit,
            action.cumulative_orbit,
        )

    def test_malformed_version_fields_and_quaternions_are_rejected(self):
        frame = bytearray(encode_camera_action_frame(self.make_action()))
        struct.pack_into(">H", frame, 4, 99)
        with self.assertRaisesRegex(
            UnsupportedCameraActionVersion, "version 99"
        ):
            decode_camera_action_frame(bytes(frame))

        valid = encode_camera_action_frame(self.make_action())
        for malformed in (valid[:-1], b"no", b"WRNG" + valid[4:]):
            with self.subTest(malformed=malformed[:8]):
                with self.assertRaises(ProtocolError):
                    decode_camera_action_frame(malformed)

        header_size = struct.calcsize(">4sHI")
        message = json.loads(valid[header_size:])
        for mutation in (
            lambda value: value.update(extra=True),
            lambda value: value.pop("sequence"),
            lambda value: value.update(cumulative_orbit=[2, 0, 0, 0]),
            lambda value: value.update(cumulative_orbit=[0, 0, 0, 0]),
            lambda value: value.update(sequence=0),
        ):
            changed = json.loads(json.dumps(message))
            mutation(changed)
            payload = json.dumps(changed, separators=(",", ":")).encode()
            changed_frame = struct.pack(">4sHI", b"ZCCA", 1, len(payload)) + payload
            with self.assertRaises(ProtocolError):
                decode_camera_action_frame(changed_frame)

        duplicate = valid[header_size:].replace(
            b'"sequence":11', b'"sequence":11,"sequence":12'
        )
        duplicate_frame = struct.pack(
            ">4sHI", b"ZCCA", 1, len(duplicate)
        ) + duplicate
        with self.assertRaisesRegex(ProtocolError, "Duplicate JSON"):
            decode_camera_action_frame(duplicate_frame)

    def test_non_commuting_composition_and_relative_checkpoint(self):
        x = quaternion_from_axis_angle((1, 0, 0), math.pi / 2)
        y = quaternion_from_axis_angle((0, 1, 0), math.pi / 2)
        cumulative = quaternion_multiply(y, x)

        sequential = rotate_vector(y, rotate_vector(x, (0, 1, 0)))
        assert_vector_close(
            self, rotate_vector(cumulative, (0, 1, 0)), sequential
        )
        assert_vector_close(
            self, rotate_vector(relative_quaternion(x, cumulative), (0, 0, 1)),
            rotate_vector(y, (0, 0, 1)),
        )

    def test_coalescer_is_bounded_allows_gaps_and_rejects_replay(self):
        coalescer = CameraActionCoalescer()
        first = CameraAction(
            4, 3, 1, 1,
            quaternion_from_axis_angle((1, 0, 0), 0.1),
        )
        latest = CameraAction(
            4, 3, 8, 12,
            quaternion_from_axis_angle((0, 1, 0), 0.2),
        )
        coalescer.push(first)
        coalescer.push(latest)
        self.assertEqual(len(coalescer), 1)
        self.assertIs(coalescer.drain(), latest)
        self.assertIsNone(coalescer.drain())

        with self.assertRaises(CameraActionSequenceError):
            coalescer.push(latest)
        with self.assertRaises(SupersededCameraActionError):
            coalescer.push(CameraAction(5, 3, 9, 13, latest.cumulative_orbit))

        coalescer.clear()
        replacement = CameraAction(5, 0, 1, 1, latest.cumulative_orbit)
        coalescer.push(replacement)
        self.assertIs(coalescer.drain(), replacement)

    def test_current_scene_check_uses_generation_and_revision(self):
        action = self.make_action()
        ensure_current_camera_action(action, 7, 2)
        for current in ((8, 2), (7, 3)):
            with self.subTest(current=current):
                with self.assertRaises(SupersededCameraActionError):
                    ensure_current_camera_action(action, *current)


if __name__ == "__main__":
    unittest.main()
