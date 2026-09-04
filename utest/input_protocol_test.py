import struct
import unittest

from zencad.runtime.input_protocol import (
    INPUT_FRAME_MAGIC,
    INPUT_PROTOCOL_VERSION,
    InputBufferFull,
    InputEvent,
    InputEventBuffer,
    InputSequenceError,
    InputState,
    UnsupportedInputVersion,
    decode_input_frame,
    encode_input_frame,
)
from zencad.runtime.scene_protocol import ProtocolError


def key_event(sequence, message_type="key_down", key="left", generation=3):
    return InputEvent(generation, sequence, message_type, {
        "key": key,
        "text": "",
        "modifiers": [],
        "repeat": False,
    })


def mouse_move(sequence, x, generation=3):
    return InputEvent(generation, sequence, "mouse_move", {
        "x": x,
        "y": 2,
        "buttons": [],
        "modifiers": [],
    })


class InputProtocolTest(unittest.TestCase):
    def test_canonical_round_trip(self):
        event = InputEvent(3, 7, "key_down", {
            "key": "a",
            "text": "A",
            "modifiers": ["alt", "shift"],
            "repeat": False,
        })
        frame = encode_input_frame(event)
        self.assertTrue(frame.startswith(INPUT_FRAME_MAGIC))
        decoded = decode_input_frame(frame)
        self.assertEqual(decoded, event)
        self.assertEqual(decoded.data["modifiers"], ("shift", "alt"))
        self.assertEqual(encode_input_frame(decoded), frame)

    def test_version_size_json_and_schema_validation(self):
        frame = encode_input_frame(key_event(1))
        header = struct.Struct(">4sHI")
        _, _, size = header.unpack_from(frame)
        with self.assertRaises(UnsupportedInputVersion):
            decode_input_frame(
                header.pack(INPUT_FRAME_MAGIC, 99, size) + frame[header.size:]
            )
        with self.assertRaises(ProtocolError):
            decode_input_frame(frame[:-1])
        with self.assertRaises(ProtocolError):
            InputEvent(3, 1, "key_down", {
                "key": "a", "text": "", "modifiers": [],
            })
        with self.assertRaises(ProtocolError):
            InputEvent(3, 1, "mouse_move", {
                "x": float("nan"), "y": 0, "buttons": [], "modifiers": [],
            })

        # A hand-written duplicate top-level property exercises the strict
        # JSON object hook; Python dictionaries cannot retain duplicate keys.
        message = (
            b'{"protocol_version":1,"message_type":"key_down",'
            b'"generation":3,"sequence":1,"sequence":2,"data":'
            b'{"key":"a","text":"","modifiers":[],"repeat":false}}'
        )
        with self.assertRaises(ProtocolError):
            decode_input_frame(
                header.pack(INPUT_FRAME_MAGIC, INPUT_PROTOCOL_VERSION, len(message))
                + message
            )

    def test_buffer_coalesces_motion_but_preserves_edges(self):
        buffer = InputEventBuffer(3, max_events=4)
        buffer.push(mouse_move(1, 1))
        buffer.push(mouse_move(2, 2))
        buffer.push(key_event(3))
        buffer.push(mouse_move(4, 4))
        buffer.push(mouse_move(5, 5))
        self.assertEqual(
            [(item.message_type, item.sequence) for item in buffer.drain()],
            [("mouse_move", 2), ("key_down", 3), ("mouse_move", 5)],
        )

    def test_buffer_is_bounded_and_never_silently_drops_edges(self):
        buffer = InputEventBuffer(3, max_events=2)
        buffer.push(key_event(1, key="a"))
        buffer.push(key_event(2, key="b"))
        self.assertFalse(buffer.push(mouse_move(3, 3)))
        with self.assertRaises(InputBufferFull):
            buffer.push(key_event(4, key="c"))
        with self.assertRaises(InputSequenceError):
            buffer.push(key_event(4, key="d"))
        with self.assertRaises(ProtocolError):
            buffer.push(key_event(5, generation=4))

    def test_input_state_keeps_state_and_all_edges(self):
        state = InputState()
        state.begin_frame((
            key_event(1, "key_down", "left"),
            key_event(2, "key_up", "left"),
            InputEvent(3, 3, "mouse_button_down", {
                "button": "left", "x": 10, "y": 11, "modifiers": [],
            }),
            InputEvent(3, 4, "mouse_wheel", {
                "dx": 0, "dy": 120, "x": 10, "y": 11,
                "modifiers": [],
            }),
        ))
        self.assertTrue(state.key_pressed("left"))
        self.assertTrue(state.key_released("left"))
        self.assertFalse(state.key_down("left"))
        self.assertTrue(state.mouse_button_down("left"))
        self.assertTrue(state.mouse_button_pressed("left"))
        self.assertEqual(state.mouse_position, (10.0, 11.0))
        self.assertEqual(state.wheel_delta, (0.0, 120.0))

        state.begin_frame(())
        self.assertFalse(state.key_pressed("left"))
        self.assertFalse(state.key_released("left"))
        self.assertTrue(state.mouse_button_down("left"))
        self.assertEqual(state.wheel_delta, (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
