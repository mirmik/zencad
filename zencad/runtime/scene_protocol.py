"""Versioned, pickle-free transport for complete ZenCad scene snapshots."""

from dataclasses import dataclass, field
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
from types import MappingProxyType
from typing import Any, Iterable, Mapping
from uuid import uuid4

from OCP.TopoDS import TopoDS_Shape

from zencad.occ_compat import read_brep, write_brep


CURRENT_PROTOCOL_VERSION = 1
FRAME_MAGIC = b"ZCSN"
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_PAYLOAD_COUNT = 1_000_000
INLINE_FRAME_LIMIT = 32 * 1024 * 1024

_FRAME_HEADER = struct.Struct(">4sHII")
_PAYLOAD_LENGTH = struct.Struct(">Q")


class ProtocolError(ValueError):
    """The snapshot is malformed or violates the transport contract."""


class UnsupportedProtocolVersion(ProtocolError):
    """The sender and receiver do not share a protocol version."""


class PayloadIntegrityError(ProtocolError):
    """A payload does not match its declared size or digest."""


class SupersededGenerationError(ProtocolError):
    """A valid snapshot belongs to an iteration that is no longer current."""


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class SceneObjectRecord:
    object_id: str
    kind: str
    payload: bytes
    properties: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ProtocolError("Scene object ID must not be empty")
        if not isinstance(self.kind, str) or not self.kind:
            raise ProtocolError("Scene object kind must not be empty")
        if not isinstance(self.payload, bytes):
            raise ProtocolError("Scene object payload must be bytes")
        object.__setattr__(self, "properties", _freeze_mapping(self.properties))


@dataclass(frozen=True)
class SceneSnapshot:
    generation: int
    objects: tuple[SceneObjectRecord, ...]
    camera_policy: str = "preserve"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if (
            not isinstance(self.generation, int)
            or isinstance(self.generation, bool)
            or self.generation < 0
        ):
            raise ProtocolError("Scene generation must be non-negative")
        object.__setattr__(self, "objects", tuple(self.objects))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        if self.camera_policy not in {"preserve", "fit", "explicit"}:
            raise ProtocolError(
                f"Unsupported camera policy: {self.camera_policy!r}"
            )
        identifiers = [record.object_id for record in self.objects]
        if len(identifiers) != len(set(identifiers)):
            raise ProtocolError("Scene object IDs must be unique")


def encode_brep(shape) -> bytes:
    """Serialize a ZenCad Shape or raw TopoDS_Shape to BREP bytes."""
    if hasattr(shape, "Shape"):
        shape = shape.Shape()
    if not isinstance(shape, TopoDS_Shape):
        raise TypeError("BREP payload requires Shape or TopoDS_Shape")

    stream = io.BytesIO()
    write_brep(shape, stream)
    payload = stream.getvalue()
    if not payload:
        raise ProtocolError("OCP failed to serialize BREP payload")
    return payload


def decode_brep(payload: bytes) -> TopoDS_Shape:
    """Deserialize BREP bytes and reject corrupt or empty shapes."""
    if not isinstance(payload, bytes):
        raise TypeError("BREP payload must be bytes")

    shape = TopoDS_Shape()
    try:
        read_brep(shape, io.BytesIO(payload))
    except Exception as exception:
        raise PayloadIntegrityError("Invalid BREP payload") from exception
    if shape.IsNull():
        raise PayloadIntegrityError("Invalid BREP payload")
    return shape


def _payload_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _build_manifest(snapshot: SceneSnapshot) -> tuple[dict[str, Any], list[bytes]]:
    payloads: list[bytes] = []
    objects: list[dict[str, Any]] = []
    for index, record in enumerate(snapshot.objects):
        payloads.append(record.payload)
        objects.append({
            "id": record.object_id,
            "kind": record.kind,
            "payload_index": index,
            "payload_size": len(record.payload),
            "payload_sha256": _payload_digest(record.payload),
            "properties": dict(record.properties),
        })

    manifest = {
        "protocol_version": CURRENT_PROTOCOL_VERSION,
        "generation": snapshot.generation,
        "camera_policy": snapshot.camera_policy,
        "metadata": dict(snapshot.metadata),
        "objects": objects,
    }
    return manifest, payloads


def _encode_manifest(manifest: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exception:
        raise ProtocolError("Snapshot manifest must contain JSON values") from exception
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ProtocolError("Snapshot manifest exceeds the size limit")
    return encoded


def encode_snapshot_frame(snapshot: SceneSnapshot) -> bytes:
    """Encode one snapshot as a self-contained binary frame."""
    manifest, payloads = _build_manifest(snapshot)
    manifest_bytes = _encode_manifest(manifest)
    frame_size = (
        _FRAME_HEADER.size
        + len(manifest_bytes)
        + sum(_PAYLOAD_LENGTH.size + len(payload) for payload in payloads)
    )
    if frame_size > INLINE_FRAME_LIMIT:
        raise ProtocolError(
            "Snapshot exceeds the inline frame limit; use FileSnapshotBundle"
        )
    chunks = [
        _FRAME_HEADER.pack(
            FRAME_MAGIC,
            CURRENT_PROTOCOL_VERSION,
            len(manifest_bytes),
            len(payloads),
        ),
        manifest_bytes,
    ]
    for payload in payloads:
        chunks.extend((_PAYLOAD_LENGTH.pack(len(payload)), payload))
    return b"".join(chunks)


def _decode_manifest(data: bytes, version: int) -> dict[str, Any]:
    if version != CURRENT_PROTOCOL_VERSION:
        raise UnsupportedProtocolVersion(
            f"Unsupported scene protocol version {version}; "
            f"expected {CURRENT_PROTOCOL_VERSION}"
        )
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise ProtocolError("Invalid snapshot manifest JSON") from exception
    if not isinstance(manifest, dict):
        raise ProtocolError("Snapshot manifest must be an object")
    if manifest.get("protocol_version") != version:
        raise ProtocolError("Frame and manifest protocol versions disagree")
    return manifest


def _snapshot_from_parts(
    manifest: Mapping[str, Any], payloads: Iterable[bytes]
) -> SceneSnapshot:
    payloads = list(payloads)
    raw_objects = manifest.get("objects")
    if not isinstance(raw_objects, list):
        raise ProtocolError("Snapshot manifest objects must be a list")
    if len(raw_objects) != len(payloads):
        raise ProtocolError("Manifest object and payload counts disagree")

    records = []
    seen_payloads = set()
    for raw in raw_objects:
        if not isinstance(raw, dict):
            raise ProtocolError("Snapshot object entry must be an object")
        index = raw.get("payload_index")
        if not isinstance(index, int) or not 0 <= index < len(payloads):
            raise ProtocolError("Snapshot object has invalid payload index")
        if index in seen_payloads:
            raise ProtocolError("Snapshot payload index is used more than once")
        seen_payloads.add(index)
        payload = payloads[index]
        if raw.get("payload_size") != len(payload):
            raise PayloadIntegrityError("Snapshot payload size mismatch")
        if raw.get("payload_sha256") != _payload_digest(payload):
            raise PayloadIntegrityError("Snapshot payload digest mismatch")
        properties = raw.get("properties", {})
        if not isinstance(properties, dict):
            raise ProtocolError("Snapshot object properties must be an object")
        records.append(SceneObjectRecord(
            object_id=raw.get("id"),
            kind=raw.get("kind"),
            payload=payload,
            properties=properties,
        ))

    generation = manifest.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool):
        raise ProtocolError("Snapshot generation must be an integer")
    metadata = manifest.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ProtocolError("Snapshot metadata must be an object")
    camera_policy = manifest.get("camera_policy", "preserve")
    if not isinstance(camera_policy, str):
        raise ProtocolError("Snapshot camera policy must be a string")
    return SceneSnapshot(
        generation=generation,
        objects=tuple(records),
        camera_policy=camera_policy,
        metadata=metadata,
    )


def decode_snapshot_frame(frame: bytes) -> SceneSnapshot:
    """Decode and fully validate a binary scene frame."""
    if not isinstance(frame, bytes):
        raise TypeError("Snapshot frame must be bytes")
    if len(frame) > INLINE_FRAME_LIMIT:
        raise ProtocolError("Snapshot exceeds the inline frame limit")
    if len(frame) < _FRAME_HEADER.size:
        raise ProtocolError("Truncated snapshot frame header")

    magic, version, manifest_size, payload_count = _FRAME_HEADER.unpack_from(frame)
    if magic != FRAME_MAGIC:
        raise ProtocolError("Invalid snapshot frame magic")
    if version != CURRENT_PROTOCOL_VERSION:
        raise UnsupportedProtocolVersion(
            f"Unsupported scene protocol version {version}; "
            f"expected {CURRENT_PROTOCOL_VERSION}"
        )
    if manifest_size > MAX_MANIFEST_BYTES:
        raise ProtocolError("Snapshot manifest exceeds the size limit")
    if payload_count > MAX_PAYLOAD_COUNT:
        raise ProtocolError("Snapshot payload count exceeds the limit")

    cursor = _FRAME_HEADER.size
    manifest_end = cursor + manifest_size
    if manifest_end > len(frame):
        raise ProtocolError("Truncated snapshot manifest")
    manifest = _decode_manifest(frame[cursor:manifest_end], version)
    cursor = manifest_end

    payloads = []
    for _ in range(payload_count):
        length_end = cursor + _PAYLOAD_LENGTH.size
        if length_end > len(frame):
            raise ProtocolError("Truncated snapshot payload length")
        payload_size = _PAYLOAD_LENGTH.unpack_from(frame, cursor)[0]
        cursor = length_end
        payload_end = cursor + payload_size
        if payload_end > len(frame):
            raise ProtocolError("Truncated snapshot payload")
        payloads.append(frame[cursor:payload_end])
        cursor = payload_end
    if cursor != len(frame):
        raise ProtocolError("Unexpected bytes after snapshot payloads")

    return _snapshot_from_parts(manifest, payloads)


def ensure_current_generation(snapshot: SceneSnapshot, expected: int) -> None:
    if snapshot.generation != expected:
        raise SupersededGenerationError(
            f"Snapshot generation {snapshot.generation} is not current "
            f"generation {expected}"
        )


def select_snapshot_transport(snapshot: SceneSnapshot) -> str:
    """Choose the v1 carrier without changing the logical protocol."""
    manifest, payloads = _build_manifest(snapshot)
    manifest_bytes = _encode_manifest(manifest)
    frame_size = (
        _FRAME_HEADER.size
        + len(manifest_bytes)
        + sum(_PAYLOAD_LENGTH.size + len(payload) for payload in payloads)
    )
    return "inline" if frame_size <= INLINE_FRAME_LIMIT else "file"


class FileSnapshotBundle:
    """Atomic directory-backed representation for large snapshot payloads."""

    MANIFEST_NAME = "manifest.json"

    @staticmethod
    def _payload_name(index: int) -> str:
        return f"payload-{index:06d}.bin"

    @classmethod
    def write(cls, path, snapshot: SceneSnapshot) -> Path:
        path = Path(path)
        if path.exists():
            raise FileExistsError(path)
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        temporary = parent / f".{path.name}.{uuid4().hex}.tmp"
        manifest, payloads = _build_manifest(snapshot)
        try:
            temporary.mkdir()
            for index, payload in enumerate(payloads):
                (temporary / cls._payload_name(index)).write_bytes(payload)
            (temporary / cls.MANIFEST_NAME).write_bytes(
                _encode_manifest(manifest)
            )
            os.replace(temporary, path)
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise
        return path

    @classmethod
    def read(cls, path) -> SceneSnapshot:
        path = Path(path)
        try:
            manifest_bytes = (path / cls.MANIFEST_NAME).read_bytes()
        except OSError as exception:
            raise ProtocolError("Snapshot bundle manifest is unavailable") from exception
        if len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise ProtocolError("Snapshot manifest exceeds the size limit")
        manifest = _decode_manifest(
            manifest_bytes,
            manifest_version(manifest_bytes),
        )
        raw_objects = manifest.get("objects")
        if not isinstance(raw_objects, list):
            raise ProtocolError("Snapshot manifest objects must be a list")
        payloads = []
        for index in range(len(raw_objects)):
            try:
                payloads.append(
                    (path / cls._payload_name(index)).read_bytes()
                )
            except OSError as exception:
                raise PayloadIntegrityError(
                    f"Snapshot bundle payload {index} is unavailable"
                ) from exception
        return _snapshot_from_parts(manifest, payloads)


def manifest_version(manifest_bytes: bytes) -> int:
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise ProtocolError("Invalid snapshot manifest JSON") from exception
    if not isinstance(manifest, dict):
        raise ProtocolError("Snapshot manifest must be an object")
    version = manifest.get("protocol_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ProtocolError("Snapshot protocol version must be an integer")
    return version
