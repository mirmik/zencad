"""Resolved OCCT operations used by typed topology selectors."""

from __future__ import annotations

import math

from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.GProp import GProp_GProps
from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHELL,
    TopAbs_SOLID,
    TopAbs_VERTEX,
    TopAbs_WIRE,
)
from OCP.gp import gp_Pnt

from zencad._native.shape import Shape as ResolvedShape
from zencad.occ_compat import as_edge, as_face, as_vertex, vertex_point

from ._value_operations import Point3Value


_CURVE_KINDS = {
    "GeomAbs_Line": "line",
    "GeomAbs_Circle": "circle",
    "GeomAbs_Ellipse": "ellipse",
    "GeomAbs_Hyperbola": "hyperbola",
    "GeomAbs_Parabola": "parabola",
    "GeomAbs_BezierCurve": "bezier",
    "GeomAbs_BSplineCurve": "bspline",
    "GeomAbs_OffsetCurve": "offset",
}
_SURFACE_KINDS = {
    "GeomAbs_Plane": "plane",
    "GeomAbs_Cylinder": "cylinder",
    "GeomAbs_Cone": "cone",
    "GeomAbs_Sphere": "sphere",
    "GeomAbs_Torus": "torus",
    "GeomAbs_BezierSurface": "bezier",
    "GeomAbs_BSplineSurface": "bspline",
    "GeomAbs_SurfaceOfExtrusion": "extrusion",
    "GeomAbs_SurfaceOfRevolution": "revolution",
    "GeomAbs_OffsetSurface": "offset",
}
_TOPOLOGY_KINDS = {
    TopAbs_VERTEX: "vertex",
    TopAbs_WIRE: "wire",
    TopAbs_SHELL: "shell",
    TopAbs_SOLID: "solid",
    TopAbs_COMPSOLID: "compsolid",
    TopAbs_COMPOUND: "compound",
}


def sequence_slice(
    sequence: tuple[ResolvedShape, ...],
    start: int | None,
    stop: int | None,
    step: int | None,
) -> tuple[ResolvedShape, ...]:
    return sequence[slice(start, stop, step)]


def geometry_type(shape: ResolvedShape) -> str:
    kind = shape.Shape().ShapeType()
    if kind == TopAbs_EDGE:
        curve_kind = BRepAdaptor_Curve(as_edge(shape.Shape())).GetType().name
        return _CURVE_KINDS.get(curve_kind, "other")
    if kind == TopAbs_FACE:
        surface_kind = BRepAdaptor_Surface(as_face(shape.Shape())).GetType().name
        return _SURFACE_KINDS.get(surface_kind, "other")
    return _TOPOLOGY_KINDS.get(kind, "other")


def sequence_geometry_types(
    sequence: tuple[ResolvedShape, ...],
) -> tuple[str, ...]:
    return tuple(geometry_type(shape) for shape in sequence)


def filter_geometry_type(
    sequence: tuple[ResolvedShape, ...],
    kind: str,
) -> tuple[ResolvedShape, ...]:
    return tuple(shape for shape in sequence if geometry_type(shape) == kind)


def _direction(
    shape: ResolvedShape, *, planar_only: bool
) -> tuple[float, float, float] | None:
    kind = shape.Shape().ShapeType()
    direction = None
    if kind == TopAbs_EDGE and not planar_only:
        adaptor = BRepAdaptor_Curve(as_edge(shape.Shape()))
        curve_kind = adaptor.GetType().name
        if curve_kind == "GeomAbs_Line":
            direction = adaptor.Line().Direction()
        elif curve_kind == "GeomAbs_Circle":
            direction = adaptor.Circle().Axis().Direction()
        elif curve_kind == "GeomAbs_Ellipse":
            direction = adaptor.Ellipse().Axis().Direction()
    elif kind == TopAbs_FACE:
        adaptor = BRepAdaptor_Surface(as_face(shape.Shape()))
        surface_kind = adaptor.GetType().name
        if surface_kind == "GeomAbs_Plane":
            direction = adaptor.Plane().Axis().Direction()
        elif not planar_only and surface_kind == "GeomAbs_Cylinder":
            direction = adaptor.Cylinder().Axis().Direction()
        elif not planar_only and surface_kind == "GeomAbs_Cone":
            direction = adaptor.Cone().Axis().Direction()
        elif not planar_only and surface_kind == "GeomAbs_Torus":
            direction = adaptor.Torus().Axis().Direction()
    if direction is None:
        return None
    return (float(direction.X()), float(direction.Y()), float(direction.Z()))


def _unit(value: tuple[float, float, float], name: str) -> tuple[float, float, float]:
    length = math.sqrt(sum(item * item for item in value))
    if not math.isfinite(length) or length == 0:
        raise ValueError(f"{name} must be finite and non-zero")
    return tuple(item / length for item in value)  # type: ignore[return-value]


def filter_direction(
    sequence: tuple[ResolvedShape, ...],
    direction: tuple[float, float, float],
    tolerance: float,
    planar_only: bool,
) -> tuple[ResolvedShape, ...]:
    expected = _unit(direction, "selector direction")
    if not math.isfinite(tolerance) or tolerance < 0 or tolerance > math.pi / 2:
        raise ValueError("direction tolerance must be within [0, pi/2]")
    selected = []
    for shape in sequence:
        candidate = _direction(shape, planar_only=planar_only)
        if candidate is None:
            continue
        candidate = _unit(candidate, "geometry direction")
        cosine = min(1.0, abs(sum(a * b for a, b in zip(candidate, expected))))
        if math.acos(cosine) <= tolerance:
            selected.append(shape)
    return tuple(selected)


def _properties(shape: ResolvedShape) -> GProp_GProps:
    properties = GProp_GProps()
    kind = shape.Shape().ShapeType()
    if kind in (TopAbs_EDGE, TopAbs_WIRE):
        BRepGProp.LinearProperties_s(shape.Shape(), properties)
    elif kind in (TopAbs_FACE, TopAbs_SHELL):
        BRepGProp.SurfaceProperties_s(shape.Shape(), properties)
    elif kind in (TopAbs_SOLID, TopAbs_COMPSOLID, TopAbs_COMPOUND):
        BRepGProp.VolumeProperties_s(shape.Shape(), properties)
    else:
        raise TypeError("selector measure is undefined for this topology kind")
    return properties


def _center(shape: ResolvedShape) -> tuple[float, float, float]:
    if shape.Shape().ShapeType() == TopAbs_VERTEX:
        point = vertex_point(as_vertex(shape.Shape()))
    else:
        point = _properties(shape).CentreOfMass()
    return (float(point.X()), float(point.Y()), float(point.Z()))


def _measure(shape: ResolvedShape) -> float:
    return float(_properties(shape).Mass())


def filter_position(
    sequence: tuple[ResolvedShape, ...],
    origin: Point3Value,
    normal: tuple[float, float, float],
    tolerance: float,
) -> tuple[ResolvedShape, ...]:
    unit = _unit(normal, "selector position normal")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("position tolerance must be finite and non-negative")
    return tuple(
        shape
        for shape in sequence
        if abs(
            sum(
                (value - base) * axis
                for value, base, axis in zip(
                    _center(shape),
                    (origin.x, origin.y, origin.z),
                    unit,
                )
            )
        )
        <= tolerance
    )


def sort_axis(
    sequence: tuple[ResolvedShape, ...],
    direction: tuple[float, float, float],
    reverse: bool,
) -> tuple[ResolvedShape, ...]:
    unit = _unit(direction, "selector sort axis")
    return tuple(
        sorted(
            sequence,
            key=lambda shape: sum(
                value * axis for value, axis in zip(_center(shape), unit)
            ),
            reverse=reverse,
        )
    )


def sort_distance(
    sequence: tuple[ResolvedShape, ...],
    point: Point3Value,
    reverse: bool,
) -> tuple[ResolvedShape, ...]:
    query = BRepBuilderAPI_MakeVertex(gp_Pnt(point.x, point.y, point.z)).Vertex()

    def distance(shape: ResolvedShape) -> float:
        extrema = BRepExtrema_DistShapeShape(shape.Shape(), query)
        extrema.Perform()
        if not extrema.IsDone():
            raise ValueError("cannot compute selector distance")
        return float(extrema.Value())

    return tuple(sorted(sequence, key=distance, reverse=reverse))


def filter_measure(
    sequence: tuple[ResolvedShape, ...],
    threshold: float,
) -> tuple[ResolvedShape, ...]:
    if not math.isfinite(threshold):
        raise ValueError("selector threshold must be finite")
    return tuple(shape for shape in sequence if _measure(shape) > threshold)


def largest(sequence: tuple[ResolvedShape, ...]) -> ResolvedShape:
    if not sequence:
        raise ValueError("largest() requires a non-empty ShapeList")
    return max(sequence, key=_measure)


def only(sequence: tuple[ResolvedShape, ...]) -> ResolvedShape:
    if len(sequence) != 1:
        raise ValueError(f"only() requires exactly one shape; got {len(sequence)}")
    return sequence[0]
