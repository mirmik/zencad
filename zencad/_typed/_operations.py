"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

from typing import Callable

from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_Transform,
)
from OCP.gp import gp_Pnt
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
from OCP.TopoDS import TopoDS_Shape, TopoDS_Wire

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import _box, _sphere
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


def _point(value: Point3Value) -> gp_Pnt:
    return gp_Pnt(value.x, value.y, value.z)


def box(size: Vector3Value, center: bool) -> ResolvedShape:
    return _box(size.x, size.y, size.z, center=center)


def sphere(radius: float) -> ResolvedShape:
    return _sphere(radius)


def segment(start: Point3Value, end: Point3Value) -> ResolvedShape:
    return ResolvedShape(BRepBuilderAPI_MakeEdge(_point(start), _point(end)).Edge())


def _polygon_wire(
    points: tuple[Point3Value, ...],
    *,
    closed: bool,
) -> TopoDS_Wire:
    if len(points) < 2:
        raise ValueError("polysegment requires at least two points")
    builder = BRepBuilderAPI_MakePolygon()
    for point in points:
        builder.Add(_point(point))
    if closed:
        builder.Close()
    if not builder.IsDone():
        raise ValueError("cannot build a wire from the supplied points")
    return builder.Wire()


def polysegment(
    points: tuple[Point3Value, ...],
    closed: bool,
) -> ResolvedShape:
    return ResolvedShape(_polygon_wire(points, closed=closed))


def polygon(points: tuple[Point3Value, ...]) -> ResolvedShape:
    if len(points) < 3:
        raise ValueError("polygon requires at least three points")
    wire = _polygon_wire(points, closed=True)
    builder = BRepBuilderAPI_MakeFace(wire)
    if not builder.IsDone():
        raise ValueError("cannot build a face from the supplied points")
    return ResolvedShape(builder.Face())


def rectangle(width: float, height: float, center: bool) -> ResolvedShape:
    x0 = -width / 2 if center else 0.0
    y0 = -height / 2 if center else 0.0
    points = (
        Point3Value(x0, y0, 0.0),
        Point3Value(x0 + width, y0, 0.0),
        Point3Value(x0 + width, y0 + height, 0.0),
        Point3Value(x0, y0 + height, 0.0),
    )
    return polygon(points)


def translate(shape: ResolvedShape, vector: Vector3Value) -> ResolvedShape:
    return shape.transform(move(vector.x, vector.y, vector.z))


def transform(shape: ResolvedShape, value: TransformValue) -> ResolvedShape:
    transformed = BRepBuilderAPI_Transform(
        shape.Shape(), transform_to_ocp(value), True
    ).Shape()
    return ResolvedShape(transformed)


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left - right


def union(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left + right


def intersection(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left ^ right


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
