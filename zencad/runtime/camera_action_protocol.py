"""Versioned, pickle-free transport for cumulative camera actions."""

from dataclasses import dataclass
import json
import math
import struct
from typing import Any

from zencad.runtime.scene_protocol import ProtocolError


CAMERA_ACTION_PROTOCOL_VERSION = 1
CAMERA_ACTION_FRAME_MAGIC = b"ZCCA"
MAX_CAMERA_ACTION_FRAME_BYTES = 64 * 1024

_FRAME_HEADER = struct.Struct(">4sHI")
_ACTION_KEYS = frozenset({
    "protocol_version",
    "message_type",
    "generation",
    "scene_revision",
    "sequence",
    "action_revision",
    "cumulative_orbit",
})
_UNIT_TOLERANCE = 1e-9
IDENTITY_QUATERNION = (1.0, 0.0, 0.0, 0.0)


class UnsupportedCameraActionVersion(ProtocolError):
    """The sender and receiver do not share a CameraAction version."""


class SupersededCameraActionError(ProtocolError):
    """A valid action does not belong to the currently presented scene."""


class CameraActionSequenceError(ProtocolError):
    """Camera actions in one stream are not strictly ordered."""


def _non_negative_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProtocolError(f"{name} must be a non-negative integer")
    return value


def _positive_integer(value: Any, name: str) -> int:
    _non_negative_integer(value, name)
    if value == 0:
        raise ProtocolError(f"{name} must be positive")
    return value


def _finite_number(value: Any, name: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ProtocolError(f"{name} must be a finite number")
    return float(value)


def _require_exact_keys(value, expected, name):
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


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"Duplicate JSON property: {key!r}")
        result[key] = value
    return result


def _invalid_json_constant(value):
    raise ProtocolError(f"Invalid JSON number: {value}")


def canonical_quaternion(value, *, require_unit=False):
    """Return a normalized, sign-canonical ``(w, x, y, z)`` quaternion."""
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ProtocolError("Camera quaternion must contain four numbers")
    quaternion = tuple(
        _finite_number(component, "Camera quaternion component")
        for component in value
    )
    norm = math.sqrt(sum(component * component for component in quaternion))
    if norm == 0:
        raise ProtocolError("Camera quaternion must be non-zero")
    if require_unit and not math.isclose(
        norm, 1.0, rel_tol=_UNIT_TOLERANCE, abs_tol=_UNIT_TOLERANCE
    ):
        raise ProtocolError("Camera quaternion must be normalized")
    normalized = tuple(component / norm for component in quaternion)
    first = next((component for component in normalized if component != 0), 1.0)
    if first < 0:
        normalized = tuple(-component for component in normalized)
    return tuple(0.0 if component == 0 else component for component in normalized)


def quaternion_multiply(left, right):
    """Compose rotations so ``right`` is applied before ``left``."""
    lw, lx, ly, lz = canonical_quaternion(left)
    rw, rx, ry, rz = canonical_quaternion(right)
    return canonical_quaternion((
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    ))


def quaternion_inverse(value):
    w, x, y, z = canonical_quaternion(value)
    return canonical_quaternion((w, -x, -y, -z))


def quaternion_from_axis_angle(axis, angle):
    if not isinstance(axis, (tuple, list)) or len(axis) != 3:
        raise ProtocolError("Camera orbit axis must contain three numbers")
    x, y, z = (
        _finite_number(component, "Camera orbit axis component")
        for component in axis
    )
    length = math.sqrt(x * x + y * y + z * z)
    if length == 0:
        raise ProtocolError("Camera orbit axis must be non-zero")
    angle = _finite_number(angle, "Camera orbit angle")
    half = math.remainder(angle, math.tau) / 2.0
    scale = math.sin(half) / length
    return canonical_quaternion((math.cos(half), x * scale, y * scale, z * scale))


def relative_quaternion(previous, current):
    """Return the rotation advancing one cumulative checkpoint to another."""
    return quaternion_multiply(current, quaternion_inverse(previous))


def rotate_vector(quaternion, vector):
    if not isinstance(vector, (tuple, list)) or len(vector) != 3:
        raise ProtocolError("Camera vector must contain three numbers")
    vx, vy, vz = (
        _finite_number(component, "Camera vector component")
        for component in vector
    )
    w, x, y, z = canonical_quaternion(quaternion)
    # Unit-quaternion vector rotation without constructing a non-unit pure
    # quaternion (which canonical_quaternion deliberately normalizes).
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


@dataclass(frozen=True)
class CameraAction:
    """Latest cumulative runner-requested orbit for one live scene."""

    generation: int
    scene_revision: int
    sequence: int
    action_revision: int
    cumulative_orbit: tuple[float, float, float, float]

    def __post_init__(self):
        _non_negative_integer(self.generation, "CameraAction generation")
        _non_negative_integer(
            self.scene_revision, "CameraAction scene revision"
        )
        _positive_integer(self.sequence, "CameraAction sequence")
        _positive_integer(
            self.action_revision, "CameraAction action revision"
        )
        object.__setattr__(
            self,
            "cumulative_orbit",
            canonical_quaternion(self.cumulative_orbit, require_unit=True),
        )


def encode_camera_action_frame(action: CameraAction) -> bytes:
    if not isinstance(action, CameraAction):
        raise TypeError("CameraAction encoder requires a CameraAction")
    message = {
        "protocol_version": CAMERA_ACTION_PROTOCOL_VERSION,
        "message_type": "camera_action",
        "generation": action.generation,
        "scene_revision": action.scene_revision,
        "sequence": action.sequence,
        "action_revision": action.action_revision,
        "cumulative_orbit": list(action.cumulative_orbit),
    }
    try:
        payload = json.dumps(
            message,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exception:
        raise ProtocolError("CameraAction must contain JSON values") from exception
    frame = _FRAME_HEADER.pack(
        CAMERA_ACTION_FRAME_MAGIC,
        CAMERA_ACTION_PROTOCOL_VERSION,
        len(payload),
    ) + payload
    if len(frame) > MAX_CAMERA_ACTION_FRAME_BYTES:
        raise ProtocolError("CameraAction frame exceeds the size limit")
    return frame


def decode_camera_action_frame(frame: bytes) -> CameraAction:
    if not isinstance(frame, bytes):
        raise TypeError("CameraAction frame must be bytes")
    if len(frame) > MAX_CAMERA_ACTION_FRAME_BYTES:
        raise ProtocolError("CameraAction frame exceeds the size limit")
    if len(frame) < _FRAME_HEADER.size:
        raise ProtocolError("Truncated CameraAction frame header")
    magic, version, payload_size = _FRAME_HEADER.unpack_from(frame)
    if magic != CAMERA_ACTION_FRAME_MAGIC:
        raise ProtocolError("Invalid CameraAction frame magic")
    if version != CAMERA_ACTION_PROTOCOL_VERSION:
        raise UnsupportedCameraActionVersion(
            f"Unsupported CameraAction protocol version {version}; "
            f"expected {CAMERA_ACTION_PROTOCOL_VERSION}"
        )
    if payload_size != len(frame) - _FRAME_HEADER.size:
        raise ProtocolError("CameraAction frame size mismatch")
    try:
        message = json.loads(
            frame[_FRAME_HEADER.size:].decode("utf-8"),
            object_pairs_hook=_json_object,
            parse_constant=_invalid_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exception:
        raise ProtocolError("Invalid CameraAction JSON") from exception
    if not isinstance(message, dict):
        raise ProtocolError("CameraAction message must be an object")
    _require_exact_keys(message, _ACTION_KEYS, "CameraAction message")
    if message["protocol_version"] != version:
        raise ProtocolError("Frame and CameraAction protocol versions disagree")
    if message["message_type"] != "camera_action":
        raise ProtocolError("CameraAction message has an invalid type")
    return CameraAction(
        generation=message["generation"],
        scene_revision=message["scene_revision"],
        sequence=message["sequence"],
        action_revision=message["action_revision"],
        cumulative_orbit=message["cumulative_orbit"],
    )


def ensure_current_camera_action(action, expected_generation, expected_revision):
    if not isinstance(action, CameraAction):
        raise TypeError("Current-scene validation requires a CameraAction")
    _non_negative_integer(expected_generation, "Expected generation")
    _non_negative_integer(expected_revision, "Expected scene revision")
    if (
        action.generation != expected_generation
        or action.scene_revision != expected_revision
    ):
        raise SupersededCameraActionError(
            "CameraAction targets generation/revision "
            f"{action.generation}/{action.scene_revision}, current scene is "
            f"{expected_generation}/{expected_revision}"
        )


class CameraActionCoalescer:
    """Retain at most the newest cumulative action for one scene stream."""

    def __init__(self):
        self.clear()

    def __len__(self):
        return 0 if self._pending is None else 1

    @property
    def last_sequence(self):
        return self._last_sequence

    def clear(self):
        self._generation = None
        self._scene_revision = None
        self._last_sequence = None
        self._last_action_revision = None
        self._pending = None

    def push(self, action: CameraAction):
        if not isinstance(action, CameraAction):
            raise TypeError("CameraActionCoalescer requires CameraAction values")
        identity = (action.generation, action.scene_revision)
        current = (self._generation, self._scene_revision)
        if self._generation is None:
            self._generation, self._scene_revision = identity
        elif identity != current:
            raise SupersededCameraActionError(
                "Cannot coalesce actions from different scene revisions"
            )
        if (
            self._last_sequence is not None
            and action.sequence <= self._last_sequence
        ):
            raise CameraActionSequenceError(
                "CameraAction sequence must increase strictly"
            )
        if (
            self._last_action_revision is not None
            and action.action_revision <= self._last_action_revision
        ):
            raise CameraActionSequenceError(
                "CameraAction revision must increase strictly"
            )
        self._last_sequence = action.sequence
        self._last_action_revision = action.action_revision
        self._pending = action

    def drain(self):
        action, self._pending = self._pending, None
        return action
