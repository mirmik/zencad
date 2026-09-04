"""Versioned, pickle-free input transport for managed animations."""

from collections import deque
from dataclasses import dataclass, field
import json
import math
import struct
from types import MappingProxyType
from typing import Any, Mapping

from zencad.runtime.scene_protocol import ProtocolError


INPUT_PROTOCOL_VERSION = 1
INPUT_FRAME_MAGIC = b"ZCIN"
MAX_INPUT_FRAME_BYTES = 64 * 1024
MAX_INPUT_BUFFER_EVENTS = 256

_FRAME_HEADER = struct.Struct(">4sHI")
_MESSAGE_KEYS = frozenset({
    "protocol_version", "message_type", "generation", "sequence", "data",
})
_EVENT_TYPES = frozenset({
    "key_down",
    "key_up",
    "mouse_move",
    "mouse_button_down",
    "mouse_button_up",
    "mouse_wheel",
})
_KEY_FIELDS = frozenset({"key", "text", "modifiers", "repeat"})
_MOUSE_MOVE_FIELDS = frozenset({"x", "y", "buttons", "modifiers"})
_MOUSE_BUTTON_FIELDS = frozenset({"button", "x", "y", "modifiers"})
_MOUSE_WHEEL_FIELDS = frozenset({"dx", "dy", "x", "y", "modifiers"})
_MODIFIERS = ("shift", "control", "alt", "meta")
_BUTTONS = ("left", "middle", "right", "back", "forward")


class UnsupportedInputVersion(ProtocolError):
    """The GUI and runner do not share an InputEvent version."""


class InputSequenceError(ProtocolError):
    """Input events for one generation are not strictly ordered."""


class InputBufferFull(ProtocolError):
    """The bounded queue cannot retain another discrete input edge."""


def _non_negative_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProtocolError(f"{name} must be a non-negative integer")
    return value


def _finite_number(value: Any, name: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ProtocolError(f"{name} must be a finite number")
    return float(value)


def _text(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ProtocolError(f"{name} must be a string")
    if len(value.encode("utf-8")) > maximum:
        raise ProtocolError(f"{name} exceeds the size limit")
    return value


def _require_exact_keys(value: Mapping[str, Any], expected, name: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing {missing!r}")
        if unknown:
            details.append(f"unknown {unknown!r}")
        raise ProtocolError(f"{name} has invalid fields: {', '.join(details)}")


def _names(value: Any, name: str, allowed: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ProtocolError(f"{name} must be a list")
    if any(not isinstance(item, str) or item not in allowed for item in value):
        raise ProtocolError(f"{name} contains an unsupported value")
    if len(value) != len(set(value)):
        raise ProtocolError(f"{name} must not contain duplicates")
    return tuple(item for item in allowed if item in value)


def _normalize_data(message_type: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolError("InputEvent data must be an object")
    if message_type in {"key_down", "key_up"}:
        _require_exact_keys(value, _KEY_FIELDS, "Keyboard InputEvent")
        key = _text(value["key"], "InputEvent key", 128)
        if not key:
            raise ProtocolError("InputEvent key must not be empty")
        if not isinstance(value["repeat"], bool):
            raise ProtocolError("InputEvent repeat must be a boolean")
        result = {
            "key": key,
            "text": _text(value["text"], "InputEvent text", 1024),
            "modifiers": _names(value["modifiers"], "modifiers", _MODIFIERS),
            "repeat": value["repeat"],
        }
    elif message_type == "mouse_move":
        _require_exact_keys(value, _MOUSE_MOVE_FIELDS, "Mouse move InputEvent")
        result = {
            "x": _finite_number(value["x"], "mouse x"),
            "y": _finite_number(value["y"], "mouse y"),
            "buttons": _names(value["buttons"], "buttons", _BUTTONS),
            "modifiers": _names(value["modifiers"], "modifiers", _MODIFIERS),
        }
    elif message_type in {"mouse_button_down", "mouse_button_up"}:
        _require_exact_keys(value, _MOUSE_BUTTON_FIELDS, "Mouse button InputEvent")
        button = value["button"]
        if not isinstance(button, str) or button not in _BUTTONS:
            raise ProtocolError("InputEvent button is unsupported")
        result = {
            "button": button,
            "x": _finite_number(value["x"], "mouse x"),
            "y": _finite_number(value["y"], "mouse y"),
            "modifiers": _names(value["modifiers"], "modifiers", _MODIFIERS),
        }
    elif message_type == "mouse_wheel":
        _require_exact_keys(value, _MOUSE_WHEEL_FIELDS, "Mouse wheel InputEvent")
        result = {
            "dx": _finite_number(value["dx"], "wheel dx"),
            "dy": _finite_number(value["dy"], "wheel dy"),
            "x": _finite_number(value["x"], "mouse x"),
            "y": _finite_number(value["y"], "mouse y"),
            "modifiers": _names(value["modifiers"], "modifiers", _MODIFIERS),
        }
    else:
        raise ProtocolError(f"Unsupported InputEvent type: {message_type!r}")
    return MappingProxyType(result)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"Duplicate JSON property: {key!r}")
        result[key] = value
    return result


def _invalid_json_constant(value):
    raise ProtocolError(f"Invalid JSON number: {value}")


@dataclass(frozen=True)
class InputEvent:
    """One normalized GUI event belonging to a runner generation."""

    generation: int
    sequence: int
    message_type: str
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _non_negative_integer(self.generation, "InputEvent generation")
        _non_negative_integer(self.sequence, "InputEvent sequence")
        if self.message_type not in _EVENT_TYPES:
            raise ProtocolError(
                f"Unsupported InputEvent type: {self.message_type!r}"
            )
        object.__setattr__(
            self, "data", _normalize_data(self.message_type, self.data)
        )


def encode_input_frame(event: InputEvent) -> bytes:
    """Encode an input event as one canonical UTF-8 JSON frame."""
    if not isinstance(event, InputEvent):
        raise TypeError("Input encoder requires an InputEvent")
    message = {
        "protocol_version": INPUT_PROTOCOL_VERSION,
        "message_type": event.message_type,
        "generation": event.generation,
        "sequence": event.sequence,
        "data": _plain(event.data),
    }
    encoded = json.dumps(
        message,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(encoded) > MAX_INPUT_FRAME_BYTES:
        raise ProtocolError("InputEvent exceeds the size limit")
    return _FRAME_HEADER.pack(
        INPUT_FRAME_MAGIC, INPUT_PROTOCOL_VERSION, len(encoded)
    ) + encoded


def decode_input_frame(frame: bytes) -> InputEvent:
    """Decode and strictly validate one InputEvent frame."""
    if not isinstance(frame, bytes):
        raise TypeError("InputEvent frame must be bytes")
    if len(frame) < _FRAME_HEADER.size:
        raise ProtocolError("Truncated InputEvent frame")
    magic, version, size = _FRAME_HEADER.unpack_from(frame)
    if magic != INPUT_FRAME_MAGIC:
        raise ProtocolError("Invalid InputEvent magic")
    if version != INPUT_PROTOCOL_VERSION:
        raise UnsupportedInputVersion(
            f"Unsupported InputEvent protocol version {version}"
        )
    if size > MAX_INPUT_FRAME_BYTES:
        raise ProtocolError("InputEvent exceeds the size limit")
    encoded = frame[_FRAME_HEADER.size:]
    if len(encoded) != size:
        raise ProtocolError("InputEvent frame size mismatch")
    try:
        message = json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=_json_object,
            parse_constant=_invalid_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise ProtocolError("Invalid InputEvent JSON") from exception
    if not isinstance(message, Mapping):
        raise ProtocolError("InputEvent message must be an object")
    _require_exact_keys(message, _MESSAGE_KEYS, "InputEvent message")
    if message["protocol_version"] != version:
        raise ProtocolError("InputEvent frame and message versions disagree")
    return InputEvent(
        generation=message["generation"],
        sequence=message["sequence"],
        message_type=message["message_type"],
        data=message["data"],
    )


class InputEventBuffer:
    """Bounded queue preserving edges while coalescing continuous motion."""

    def __init__(self, generation: int, max_events=MAX_INPUT_BUFFER_EVENTS):
        _non_negative_integer(generation, "Input buffer generation")
        if not isinstance(max_events, int) or isinstance(max_events, bool):
            raise ValueError("Input buffer size must be an integer")
        if max_events <= 0:
            raise ValueError("Input buffer size must be positive")
        self.generation = generation
        self.max_events = max_events
        self._events = deque()
        self._last_sequence = -1

    def push(self, event: InputEvent) -> bool:
        if not isinstance(event, InputEvent):
            raise TypeError("Input buffer requires InputEvent values")
        if event.generation != self.generation:
            raise ProtocolError("InputEvent belongs to another generation")
        if event.sequence <= self._last_sequence:
            raise InputSequenceError("InputEvent sequence must increase")
        self._last_sequence = event.sequence

        if (
            event.message_type == "mouse_move"
            and self._events
            and self._events[-1].message_type == "mouse_move"
        ):
            self._events[-1] = event
            return True
        if len(self._events) >= self.max_events:
            for index, queued in enumerate(self._events):
                if queued.message_type == "mouse_move":
                    del self._events[index]
                    break
            else:
                if event.message_type == "mouse_move":
                    return False
                raise InputBufferFull(
                    "Input queue is full of discrete events"
                )
        self._events.append(event)
        return True

    def pop_left(self) -> InputEvent | None:
        return self._events.popleft() if self._events else None

    def drain(self) -> tuple[InputEvent, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def clear(self) -> None:
        self._events.clear()

    def __len__(self):
        return len(self._events)


class InputState:
    """Qt-free persistent state plus per-animation-frame input edges."""

    def __init__(self):
        self.keys_down = frozenset()
        self.mouse_buttons = frozenset()
        self.mouse_position = None
        self.events = ()
        self.keys_pressed = frozenset()
        self.keys_released = frozenset()
        self.mouse_buttons_pressed = frozenset()
        self.mouse_buttons_released = frozenset()
        self.mouse_delta = (0.0, 0.0)
        self.wheel_delta = (0.0, 0.0)
        self.modifiers = ()
        self._last_sequence = -1

    def begin_frame(self, events=()):
        events = tuple(events)
        keys_down = set(self.keys_down)
        buttons_down = set(self.mouse_buttons)
        keys_pressed = set()
        keys_released = set()
        buttons_pressed = set()
        buttons_released = set()
        mouse_dx = mouse_dy = wheel_dx = wheel_dy = 0.0
        mouse_position = self.mouse_position

        for event in events:
            if not isinstance(event, InputEvent):
                raise TypeError("InputState requires InputEvent values")
            if event.sequence <= self._last_sequence:
                raise InputSequenceError("InputState event sequence must increase")
            self._last_sequence = event.sequence
            data = event.data
            if event.message_type == "key_down":
                if data["key"] not in keys_down:
                    keys_pressed.add(data["key"])
                keys_down.add(data["key"])
            elif event.message_type == "key_up":
                keys_down.discard(data["key"])
                keys_released.add(data["key"])
            elif event.message_type == "mouse_move":
                new_position = (data["x"], data["y"])
                if mouse_position is not None:
                    mouse_dx += new_position[0] - mouse_position[0]
                    mouse_dy += new_position[1] - mouse_position[1]
                mouse_position = new_position
                buttons_down = set(data["buttons"])
            elif event.message_type in {
                "mouse_button_down", "mouse_button_up"
            }:
                mouse_position = (data["x"], data["y"])
                if event.message_type == "mouse_button_down":
                    if data["button"] not in buttons_down:
                        buttons_pressed.add(data["button"])
                    buttons_down.add(data["button"])
                else:
                    buttons_down.discard(data["button"])
                    buttons_released.add(data["button"])
            elif event.message_type == "mouse_wheel":
                mouse_position = (data["x"], data["y"])
                wheel_dx += data["dx"]
                wheel_dy += data["dy"]
            self.modifiers = data["modifiers"]

        self.events = events
        self.keys_down = frozenset(keys_down)
        self.mouse_buttons = frozenset(buttons_down)
        self.mouse_position = mouse_position
        self.keys_pressed = frozenset(keys_pressed)
        self.keys_released = frozenset(keys_released)
        self.mouse_buttons_pressed = frozenset(buttons_pressed)
        self.mouse_buttons_released = frozenset(buttons_released)
        self.mouse_delta = (mouse_dx, mouse_dy)
        self.wheel_delta = (wheel_dx, wheel_dy)
        return self

    def key_down(self, key):
        return key in self.keys_down

    def key_pressed(self, key):
        return key in self.keys_pressed

    def key_released(self, key):
        return key in self.keys_released

    def mouse_button_down(self, button):
        return button in self.mouse_buttons

    def mouse_button_pressed(self, button):
        return button in self.mouse_buttons_pressed

    def mouse_button_released(self, button):
        return button in self.mouse_buttons_released
