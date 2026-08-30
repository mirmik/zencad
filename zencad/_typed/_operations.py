"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

from typing import Callable

from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHELL,
    TopAbs_SOLID,
    TopAbs_WIRE,
    TopAbs_ShapeEnum,
    TopAbs_VERTEX,
)
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS_Shape

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import _box
from zencad.geom.trans import move
from zencad.occ_compat import (
    as_compound,
    as_compsolid,
    as_edge,
    as_face,
    as_shell,
    as_solid,
    as_vertex,
    as_wire,
    vertex_point as ocp_vertex_point,
)
from zencad.runtime.scene_protocol import decode_brep, encode_brep

from ._transform_operations import TransformValue, transform_to_ocp
from ._value_operations import Point3Value, Vector3Value


def box(x: float, y: float | None, z: float | None, center: bool) -> ResolvedShape:
    return _box(x, y, z, center=center)


def translate(shape: ResolvedShape, vector: Vector3Value) -> ResolvedShape:
    return shape.transform(move(vector.x, vector.y, vector.z))


def transform(shape: ResolvedShape, value: TransformValue) -> ResolvedShape:
    transformed = BRepBuilderAPI_Transform(
        shape.Shape(), transform_to_ocp(value), True
    ).Shape()
    return ResolvedShape(transformed)


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left - right


def shape_from_brep(payload: bytes) -> ResolvedShape:
    """Restore an immutable BREP snapshot inside the evaluation graph."""
    if not isinstance(payload, bytes):
        raise TypeError("shape_from_brep expects bytes")
    return ResolvedShape(decode_brep(payload))


def shape_to_ocp(value: ResolvedShape) -> TopoDS_Shape:
    """Return an independent OCP snapshot, never the stored mutable wrapper."""
    if not isinstance(value, ResolvedShape):
        raise TypeError("shape_to_ocp expects a resolved ZenCad Shape")
    native = value.Shape()
    if native.IsNull():
        raise ValueError("typed topology handles cannot contain a null shape")
    return decode_brep(encode_brep(native))


def _subshapes(
    shape: ResolvedShape,
    kind: TopAbs_ShapeEnum,
    convert: Callable[[TopoDS_Shape], TopoDS_Shape],
) -> tuple[ResolvedShape, ...]:
    """Preserve the legacy TopExp_Explorer occurrence semantics."""
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("cannot enumerate a null shape")
    explorer = TopExp_Explorer(native, kind)
    values: list[ResolvedShape] = []
    while explorer.More():
        values.append(ResolvedShape(convert(explorer.Current())))
        explorer.Next()
    return tuple(values)


def vertices(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    """Return vertices unique by OCCT IsSame topology identity."""
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("cannot enumerate a null shape")
    values = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(native, TopAbs_VERTEX, values)
    return tuple(
        ResolvedShape(as_vertex(values.FindKey(index)))
        for index in range(1, values.Extent() + 1)
    )


def edges(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_EDGE, as_edge)


def wires(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_WIRE, as_wire)


def faces(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_FACE, as_face)


def shells(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_SHELL, as_shell)


def solids(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_SOLID, as_solid)


def compounds(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_COMPOUND, as_compound)


def compsolids(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_COMPSOLID, as_compsolid)


def sequence_item(sequence: tuple[ResolvedShape, ...], index: int) -> ResolvedShape:
    return sequence[index]


def mass(shape: ResolvedShape) -> float:
    return float(shape.mass())


def center(shape: ResolvedShape) -> Point3Value:
    value = shape.center()
    return Point3Value(float(value.x), float(value.y), float(value.z))


def vertex_point(shape: ResolvedShape) -> Point3Value:
    native = shape.Shape()
    if native.IsNull() or not shape.is_vertex():
        raise TypeError("vertex_point expects a non-null Vertex")
    value = ocp_vertex_point(shape.Vertex())
    return Point3Value(float(value.X()), float(value.Y()), float(value.Z()))
