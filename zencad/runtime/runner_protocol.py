"""Pickle-free control messages for isolated script generations."""

from dataclasses import dataclass, field
import json
import struct
from types import MappingProxyType
from typing import Any, Mapping

from zencad.runtime.scene_protocol import ProtocolError


RUNNER_PROTOCOL_VERSION = 1
RUNNER_MAGIC = b"ZCRN"
MAX_CONTROL_BYTES = 4 * 1024 * 1024
_HEADER = struct.Struct(">4sHI")

MESSAGE_TYPES = {
    "run",
    "started",
    "progress",
    "output",
    "scene_file",
    "ready",
    "error",
    "finished",
}


def encode_control_message(message_type: str, generation: int, **payload) -> bytes:
    if message_type not in MESSAGE_TYPES:
        raise ProtocolError(f"Unsupported runner message type: {message_type!r}")
    if (
        not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 0
    ):
        raise ProtocolError("Runner generation must be a non-negative integer")
    message = {
        "protocol_version": RUNNER_PROTOCOL_VERSION,
        "type": message_type,
        "generation": generation,
        "payload": payload,
    }
    try:
        encoded = json.dumps(
            message,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exception:
        raise ProtocolError("Runner message must contain JSON values") from exception
    if len(encoded) > MAX_CONTROL_BYTES:
        raise ProtocolError("Runner control message exceeds the size limit")
    return _HEADER.pack(
        RUNNER_MAGIC,
        RUNNER_PROTOCOL_VERSION,
        len(encoded),
    ) + encoded


def decode_control_message(frame: bytes) -> tuple[str, int, dict[str, Any]]:
    if not isinstance(frame, bytes):
        raise TypeError("Runner control frame must be bytes")
    if len(frame) < _HEADER.size:
        raise ProtocolError("Truncated runner control frame")
    magic, version, size = _HEADER.unpack_from(frame)
    if magic != RUNNER_MAGIC:
        raise ProtocolError("Invalid runner control magic")
    if version != RUNNER_PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported runner protocol version {version}")
    if size > MAX_CONTROL_BYTES:
        raise ProtocolError("Runner control message exceeds the size limit")
    data = frame[_HEADER.size:]
    if len(data) != size:
        raise ProtocolError("Runner control frame size mismatch")
    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise ProtocolError("Invalid runner control JSON") from exception
    if not isinstance(message, dict):
        raise ProtocolError("Runner control message must be an object")
    if message.get("protocol_version") != version:
        raise ProtocolError("Runner frame and message versions disagree")
    message_type = message.get("type")
    if message_type not in MESSAGE_TYPES:
        raise ProtocolError(f"Unsupported runner message type: {message_type!r}")
    generation = message.get("generation")
    if (
        not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 0
    ):
        raise ProtocolError("Runner generation must be a non-negative integer")
    payload = message.get("payload")
    if not isinstance(payload, dict):
        raise ProtocolError("Runner message payload must be an object")
    return message_type, generation, payload


@dataclass(frozen=True)
class RunnerMessage:
    message_type: str
    generation: int
    payload: Mapping[str, Any] = field(default_factory=dict)
    snapshot: Any = None
    scene_patch: Any = None
    camera_action: Any = None

    def __post_init__(self):
        if (
            self.message_type not in MESSAGE_TYPES
            and self.message_type not in {"scene", "scene_patch", "camera_action"}
        ):
            raise ProtocolError(
                f"Unsupported runner message type: {self.message_type!r}"
            )
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
