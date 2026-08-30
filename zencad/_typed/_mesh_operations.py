"""Resolved immutable mesh values and OCCT/display boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from OCP.Poly import Poly_Triangle, Poly_Triangulation
from OCP.gp import gp_Dir, gp_Pnt

from zencad.geom.mesh import MeshData as LegacyMeshData
from zencad.geom.mesh import to_mesh as legacy_to_mesh
from zencad.geom.mesh import validated_mesh_data
from zencad.geom.shape import Shape as ResolvedShape
from zencad.runtime.scene_protocol import encode_mesh

from ._bound_operations import BoundaryBoxValue


VectorRow = tuple[float, float, float]
TriangleRow = tuple[int, int, int]

_MESH_MAGIC = b"ZCTM"
_MESH_VERSION = 1
_MESH_HEADER = struct.Struct(">4sB3xIIQ")
_MESH_VERTEX = struct.Struct(">6d")
_MESH_TRIANGLE = struct.Struct(">IIII")
_MAX_U32 = (1 << 32) - 1
_MAX_U64 = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class MeshValue:
    """Validated tuple-backed indexed mesh with face provenance."""

    positions: tuple[VectorRow, ...]
    normals: tuple[VectorRow, ...]
    triangles: tuple[TriangleRow, ...]
    triangle_face_ids: tuple[int, ...]
    dropped_triangles: int = 0

    def __post_init__(self) -> None:
        _validate_mesh_value(self)

    def __evalcache_key__(self) -> bytes:
        return b"zencad-typed-mesh-value-v1\x00" + encode_mesh_value(self)


def _validate_mesh_value(value: MeshValue) -> None:
    if not value.positions:
        raise ValueError("mesh must contain at least one vertex")
    if not value.triangles:
        raise ValueError("mesh must contain at least one triangle")
    if len(value.normals) != len(value.positions):
        raise ValueError("mesh must have exactly one normal per vertex")
    if len(value.triangle_face_ids) != len(value.triangles):
        raise ValueError("mesh must have exactly one face ID per triangle")
    if len(value.positions) > _MAX_U32 or len(value.triangles) > _MAX_U32:
        raise ValueError("mesh exceeds the typed codec size limit")
    if (
        type(value.dropped_triangles) is not int
        or not 0 <= value.dropped_triangles <= _MAX_U64
    ):
        raise ValueError("dropped triangle count must be a non-negative integer")

    for name, rows in (("position", value.positions), ("normal", value.normals)):
        for row in rows:
            if len(row) != 3 or any(
                type(component) is not float or not math.isfinite(component)
                for component in row
            ):
                raise ValueError(f"every mesh {name} must contain three finite floats")
    for normal in value.normals:
        if sum(component * component for component in normal) <= 1e-30:
            raise ValueError("mesh normals must be non-zero")

    for triangle in value.triangles:
        if len(triangle) != 3 or any(type(index) is not int for index in triangle):
            raise ValueError("every mesh triangle must contain three integer indices")
        if len(set(triangle)) != 3 or any(
            index < 0 or index >= len(value.positions) for index in triangle
        ):
            raise ValueError("mesh triangle contains invalid vertex indices")
    if any(
        type(face_id) is not int or not 0 <= face_id <= _MAX_U32
        for face_id in value.triangle_face_ids
    ):
        raise ValueError("mesh face IDs must be non-negative integers")


def mesh_from_data(
    positions: object,
    normals: object,
    triangles: object,
    triangle_face_ids: object,
    dropped_triangles: int,
) -> MeshValue:
    legacy = LegacyMeshData(
        positions=positions,  # type: ignore[arg-type]
        normals=normals,  # type: ignore[arg-type]
        triangles=triangles,  # type: ignore[arg-type]
        triangle_face_ids=triangle_face_ids,  # type: ignore[arg-type]
        dropped_triangles=dropped_triangles,
    )
    normalized_positions, normalized_normals, normalized_triangles = (
        validated_mesh_data(legacy)
    )
    try:
        normalized_face_ids = tuple(int(face_id) for face_id in triangle_face_ids)  # type: ignore[union-attr]
    except (TypeError, ValueError) as exception:
        raise ValueError("mesh face IDs must be iterable integers") from exception
    if any(
        isinstance(face_id, bool) or not isinstance(face_id, int)
        for face_id in triangle_face_ids  # type: ignore[union-attr]
    ):
        raise ValueError("mesh face IDs must be non-negative integers")
    return MeshValue(
        positions=normalized_positions,
        normals=normalized_normals,
        triangles=normalized_triangles,
        triangle_face_ids=normalized_face_ids,
        dropped_triangles=dropped_triangles,
    )


def mesh_shape(
    shape: ResolvedShape,
    linear_deflection: float,
    angular_deflection: float,
    crease_angle: float,
    relative: bool,
    parallel: bool,
    weld_tolerance: float | None,
) -> MeshValue:
    mesh = legacy_to_mesh(
        shape,
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
        crease_angle=crease_angle,
        relative=relative,
        parallel=parallel,
        weld_tolerance=weld_tolerance,
    )
    return mesh_from_data(
        mesh.positions,
        mesh.normals,
        mesh.triangles,
        mesh.triangle_face_ids,
        mesh.dropped_triangles,
    )


def valid_mesh(value: MeshValue) -> bool:
    try:
        _validate_mesh_value(value)
    except (TypeError, ValueError):
        return False
    return True


def mesh_boundary_box(value: MeshValue) -> BoundaryBoxValue:
    xs, ys, zs = zip(*value.positions)
    return BoundaryBoxValue((min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))


def mesh_to_poly_triangulation(value: MeshValue) -> Poly_Triangulation:
    triangulation = Poly_Triangulation(
        len(value.positions),
        len(value.triangles),
        False,
        True,
    )
    for index, (position, normal) in enumerate(zip(value.positions, value.normals), 1):
        triangulation.SetNode(index, gp_Pnt(*position))
        triangulation.SetNormal(index, gp_Dir(*normal))
    for index, triangle in enumerate(value.triangles, 1):
        triangulation.SetTriangle(
            index,
            Poly_Triangle(*(vertex + 1 for vertex in triangle)),
        )
    triangulation.UpdateCachedMinMax()
    return triangulation


def mesh_display_payload(value: MeshValue) -> bytes:
    return encode_mesh(
        LegacyMeshData(
            positions=value.positions,
            normals=value.normals,
            triangles=value.triangles,
            triangle_face_ids=value.triangle_face_ids,
            dropped_triangles=value.dropped_triangles,
        )
    )


def encode_mesh_value(value: MeshValue) -> bytes:
    _validate_mesh_value(value)
    parts = [
        _MESH_HEADER.pack(
            _MESH_MAGIC,
            _MESH_VERSION,
            len(value.positions),
            len(value.triangles),
            value.dropped_triangles,
        )
    ]
    parts.extend(
        _MESH_VERTEX.pack(*(position + normal))
        for position, normal in zip(value.positions, value.normals)
    )
    parts.extend(
        _MESH_TRIANGLE.pack(*(triangle + (face_id,)))
        for triangle, face_id in zip(value.triangles, value.triangle_face_ids)
    )
    return b"".join(parts)


def decode_mesh_value(payload: bytes) -> MeshValue:
    if not isinstance(payload, bytes) or len(payload) < _MESH_HEADER.size:
        raise ValueError("invalid typed MeshData payload")
    magic, version, vertex_count, triangle_count, dropped = _MESH_HEADER.unpack_from(
        payload
    )
    if magic != _MESH_MAGIC or version != _MESH_VERSION:
        raise ValueError("unsupported typed MeshData payload")
    expected = (
        _MESH_HEADER.size
        + vertex_count * _MESH_VERTEX.size
        + triangle_count * _MESH_TRIANGLE.size
    )
    if len(payload) != expected:
        raise ValueError("invalid typed MeshData payload size")
    cursor = _MESH_HEADER.size
    positions: list[VectorRow] = []
    normals: list[VectorRow] = []
    for _ in range(vertex_count):
        row = _MESH_VERTEX.unpack_from(payload, cursor)
        cursor += _MESH_VERTEX.size
        positions.append((row[0], row[1], row[2]))
        normals.append((row[3], row[4], row[5]))
    triangles: list[TriangleRow] = []
    face_ids: list[int] = []
    for _ in range(triangle_count):
        row = _MESH_TRIANGLE.unpack_from(payload, cursor)
        cursor += _MESH_TRIANGLE.size
        triangles.append((row[0], row[1], row[2]))
        face_ids.append(row[3])
    return MeshValue(
        positions=tuple(positions),
        normals=tuple(normals),
        triangles=tuple(triangles),
        triangle_face_ids=tuple(face_ids),
        dropped_triangles=dropped,
    )
