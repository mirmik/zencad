"""Versioned, pickle-free transport for live scene property updates."""

from collections import OrderedDict
from dataclasses import dataclass, field
import json
import math
import struct
from types import MappingProxyType
from typing import Any, Mapping

from zencad.runtime.scene_protocol import ProtocolError


SCENE_PATCH_PROTOCOL_VERSION = 1
SCENE_PATCH_FRAME_MAGIC = b"ZCPT"
MAX_SCENE_PATCH_FRAME_BYTES = 4 * 1024 * 1024
MAX_SCENE_PATCH_UPDATES = 100_000
MAX_SCENE_PATCH_OBJECT_ID_BYTES = 512

_FRAME_HEADER = struct.Struct(">4sHI")
_PATCH_KEYS = frozenset({
    "protocol_version",
    "message_type",
    "generation",
    "scene_revision",
    "sequence",
    "updates",
})
_UPDATE_KEYS = frozenset({"object_id", "properties"})
_PROPERTY_KEYS = frozenset({
    "transform",
    "visible",
    "color",
    "border_color",
    "wire_color",
})
_TRANSFORM_KEYS = frozenset({"scale", "rotation", "translation"})


class UnsupportedScenePatchVersion(ProtocolError):
    """The sender and receiver do not share a ScenePatch version."""


class SupersededScenePatchError(ProtocolError):
    """A valid patch does not belong to the currently presented scene."""


class ScenePatchSequenceError(ProtocolError):
    """Patches in one coalescing stream are not strictly ordered."""


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


def _number_tuple(value: Any, name: str, size: int) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ProtocolError(f"{name} must contain {size} numbers")
    return tuple(
        _finite_number(component, f"{name} component")
        for component in value
    )


def _rgba(value: Any, name: str) -> tuple[float, float, float, float]:
    result = _number_tuple(value, name, 4)
    if any(component < 0 or component > 1 for component in result):
        raise ProtocolError(f"{name} components must be in [0, 1]")
    return result


def _transform(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolError("transform must be an object")
    if set(value) != _TRANSFORM_KEYS:
        raise ProtocolError(
            "transform must contain exactly scale, rotation, and translation"
        )
    scale = _finite_number(value["scale"], "transform scale")
    if scale == 0:
        raise ProtocolError("transform scale must be non-zero")
    rotation = _number_tuple(
        value["rotation"], "transform rotation", 4
    )
    if not any(rotation):
        raise ProtocolError("transform rotation quaternion must be non-zero")
    return MappingProxyType({
        "scale": scale,
        "rotation": rotation,
        "translation": _number_tuple(
            value["translation"], "transform translation", 3
        ),
    })


def _properties(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolError("ScenePatch properties must be an object")
    if not value:
        raise ProtocolError("ScenePatch update must change at least one property")
    unknown = set(value) - _PROPERTY_KEYS
    if unknown:
        raise ProtocolError(
            f"Unsupported ScenePatch property: {sorted(unknown)[0]!r}"
        )

    normalized: dict[str, Any] = {}
    for name, raw in value.items():
        if name == "transform":
            normalized[name] = _transform(raw)
        elif name == "visible":
            if not isinstance(raw, bool):
                raise ProtocolError("visible must be a boolean")
            normalized[name] = raw
        else:
            normalized[name] = _rgba(raw, name)
    return MappingProxyType(normalized)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
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
class SceneObjectPatch:
    """Absolute property values for one object in the committed snapshot."""

    object_id: str
    properties: Mapping[str, Any]

    def __post_init__(self):
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ProtocolError("ScenePatch object ID must not be empty")
        if len(self.object_id.encode("utf-8")) > MAX_SCENE_PATCH_OBJECT_ID_BYTES:
            raise ProtocolError("ScenePatch object ID exceeds the size limit")
        object.__setattr__(self, "properties", _properties(self.properties))


@dataclass(frozen=True)
class ScenePatch:
    """One ordered, coalescible batch of absolute scene property updates."""

    generation: int
    scene_revision: int
    sequence: int
    updates: tuple[SceneObjectPatch, ...] = field(default_factory=tuple)

    def __post_init__(self):
        _non_negative_integer(self.generation, "ScenePatch generation")
        _non_negative_integer(self.scene_revision, "ScenePatch scene revision")
        _non_negative_integer(self.sequence, "ScenePatch sequence")
        object.__setattr__(self, "updates", tuple(self.updates))
        if len(self.updates) > MAX_SCENE_PATCH_UPDATES:
            raise ProtocolError("ScenePatch update count exceeds the limit")
        if any(not isinstance(update, SceneObjectPatch) for update in self.updates):
            raise ProtocolError("ScenePatch updates must be SceneObjectPatch values")
        object_ids = [update.object_id for update in self.updates]
        if len(object_ids) != len(set(object_ids)):
            raise ProtocolError("ScenePatch object IDs must be unique")


def encode_scene_patch_frame(patch: ScenePatch) -> bytes:
    """Encode a patch as one canonical UTF-8 JSON frame."""
    if not isinstance(patch, ScenePatch):
        raise TypeError("ScenePatch encoder requires a ScenePatch")
    message = {
        "protocol_version": SCENE_PATCH_PROTOCOL_VERSION,
        "message_type": "scene_patch",
        "generation": patch.generation,
        "scene_revision": patch.scene_revision,
        "sequence": patch.sequence,
        "updates": [
            {
                "object_id": update.object_id,
                "properties": _plain(update.properties),
            }
            for update in patch.updates
        ],
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
        raise ProtocolError("ScenePatch must contain JSON values") from exception
    frame = _FRAME_HEADER.pack(
        SCENE_PATCH_FRAME_MAGIC,
        SCENE_PATCH_PROTOCOL_VERSION,
        len(payload),
    ) + payload
    if len(frame) > MAX_SCENE_PATCH_FRAME_BYTES:
        raise ProtocolError("ScenePatch frame exceeds the size limit")
    return frame


def decode_scene_patch_frame(frame: bytes) -> ScenePatch:
    """Decode and fully validate a ScenePatch before returning it."""
    if not isinstance(frame, bytes):
        raise TypeError("ScenePatch frame must be bytes")
    if len(frame) > MAX_SCENE_PATCH_FRAME_BYTES:
        raise ProtocolError("ScenePatch frame exceeds the size limit")
    if len(frame) < _FRAME_HEADER.size:
        raise ProtocolError("Truncated ScenePatch frame header")

    magic, version, payload_size = _FRAME_HEADER.unpack_from(frame)
    if magic != SCENE_PATCH_FRAME_MAGIC:
        raise ProtocolError("Invalid ScenePatch frame magic")
    if version != SCENE_PATCH_PROTOCOL_VERSION:
        raise UnsupportedScenePatchVersion(
            f"Unsupported ScenePatch protocol version {version}; "
            f"expected {SCENE_PATCH_PROTOCOL_VERSION}"
        )
    if payload_size != len(frame) - _FRAME_HEADER.size:
        raise ProtocolError("ScenePatch frame size mismatch")

    try:
        message = json.loads(
            frame[_FRAME_HEADER.size:].decode("utf-8"),
            object_pairs_hook=_json_object,
            parse_constant=_invalid_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exception:
        raise ProtocolError("Invalid ScenePatch JSON") from exception
    if not isinstance(message, dict):
        raise ProtocolError("ScenePatch message must be an object")
    _require_exact_keys(message, _PATCH_KEYS, "ScenePatch message")
    if message["protocol_version"] != version:
        raise ProtocolError("Frame and ScenePatch protocol versions disagree")
    if message["message_type"] != "scene_patch":
        raise ProtocolError("ScenePatch message has an invalid type")

    raw_updates = message["updates"]
    if not isinstance(raw_updates, list):
        raise ProtocolError("ScenePatch updates must be a list")
    if len(raw_updates) > MAX_SCENE_PATCH_UPDATES:
        raise ProtocolError("ScenePatch update count exceeds the limit")
    updates = []
    for raw in raw_updates:
        if not isinstance(raw, dict):
            raise ProtocolError("ScenePatch update must be an object")
        _require_exact_keys(raw, _UPDATE_KEYS, "ScenePatch update")
        updates.append(SceneObjectPatch(
            object_id=raw["object_id"],
            properties=raw["properties"],
        ))
    return ScenePatch(
        generation=message["generation"],
        scene_revision=message["scene_revision"],
        sequence=message["sequence"],
        updates=tuple(updates),
    )


def ensure_current_scene_patch(
    patch: ScenePatch,
    expected_generation: int,
    expected_scene_revision: int,
) -> None:
    """Reject stale data before any GUI-side object lookup or materialization."""
    if not isinstance(patch, ScenePatch):
        raise TypeError("Current-scene validation requires a ScenePatch")
    _non_negative_integer(expected_generation, "Expected generation")
    _non_negative_integer(expected_scene_revision, "Expected scene revision")
    if (
        patch.generation != expected_generation
        or patch.scene_revision != expected_scene_revision
    ):
        raise SupersededScenePatchError(
            "ScenePatch targets generation/revision "
            f"{patch.generation}/{patch.scene_revision}, current scene is "
            f"{expected_generation}/{expected_scene_revision}"
        )


class ScenePatchCoalescer:
    """Bound pending live state while preserving latest absolute properties."""

    def __init__(self, max_objects: int = MAX_SCENE_PATCH_UPDATES):
        if (
            not isinstance(max_objects, int)
            or isinstance(max_objects, bool)
            or max_objects <= 0
            or max_objects > MAX_SCENE_PATCH_UPDATES
        ):
            raise ValueError(
                f"max_objects must be in [1, {MAX_SCENE_PATCH_UPDATES}]"
            )
        self.max_objects = max_objects
        self._generation: int | None = None
        self._scene_revision: int | None = None
        self._last_sequence: int | None = None
        self._pending: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def __len__(self):
        return len(self._pending)

    @property
    def last_sequence(self):
        return self._last_sequence

    def clear(self):
        """Forget the pending batch and its stream identity."""
        self._generation = None
        self._scene_revision = None
        self._last_sequence = None
        self._pending.clear()

    def push(self, patch: ScenePatch) -> None:
        if not isinstance(patch, ScenePatch):
            raise TypeError("ScenePatchCoalescer requires ScenePatch values")
        identity = (patch.generation, patch.scene_revision)
        current_identity = (self._generation, self._scene_revision)
        if self._generation is None:
            self._generation, self._scene_revision = identity
        elif identity != current_identity:
            raise SupersededScenePatchError(
                "Cannot coalesce patches from different scene revisions"
            )
        if self._last_sequence is not None and patch.sequence <= self._last_sequence:
            raise ScenePatchSequenceError(
                "ScenePatch sequence must increase strictly"
            )

        new_ids = {
            update.object_id
            for update in patch.updates
            if update.object_id not in self._pending
        }
        if len(self._pending) + len(new_ids) > self.max_objects:
            raise ProtocolError("ScenePatch coalescer object limit exceeded")

        for update in patch.updates:
            state = self._pending.setdefault(update.object_id, {})
            state.update(update.properties)
        self._last_sequence = patch.sequence

    def drain(self) -> ScenePatch | None:
        """Return one latest-state patch and retain ordering for later pushes."""
        if not self._pending:
            return None
        patch = ScenePatch(
            generation=self._generation,
            scene_revision=self._scene_revision,
            sequence=self._last_sequence,
            updates=tuple(
                SceneObjectPatch(object_id, properties)
                for object_id, properties in self._pending.items()
            ),
        )
        self._pending.clear()
        return patch
