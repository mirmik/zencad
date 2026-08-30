"""Resolved operations and immutable snapshots for typed curves."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math

from OCP.GCE2d import GCE2d_MakeSegment
from OCP.Geom import Geom_Circle, Geom_Curve, Geom_Ellipse, Geom_Line
from OCP.Geom2d import Geom2d_Curve, Geom2d_Ellipse, Geom2d_TrimmedCurve
from OCP.GeomTools import GeomTools_Curve2dSet, GeomTools_CurveSet
from OCP.gp import (
    gp_Ax2,
    gp_Ax2d,
    gp_Dir,
    gp_Dir2d,
    gp_Pnt,
    gp_Pnt2d,
    gp_Vec,
    gp_Vec2d,
)

from ._value_operations import (
    Point2Value,
    Point3Value,
    Vector2Value,
    Vector3Value,
)


@dataclass(frozen=True, slots=True)
class CurveValue:
    """Immutable OCCT compact-format snapshot of a three-dimensional curve."""

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes) or not self.data:
            raise TypeError("CurveValue data must be non-empty bytes")

    def __evalcache_key__(self) -> bytes:
        return b"zencad-curve-value-v1\x00" + self.data


@dataclass(frozen=True, slots=True)
class Curve2Value:
    """Immutable OCCT compact-format snapshot of a two-dimensional curve."""

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes) or not self.data:
            raise TypeError("Curve2Value data must be non-empty bytes")

    def __evalcache_key__(self) -> bytes:
        return b"zencad-curve2-value-v1\x00" + self.data


def curve_from_ocp(value: Geom_Curve) -> CurveValue:
    if not isinstance(value, Geom_Curve):
        raise TypeError("curve_from_ocp expects Geom_Curve")
    stream = BytesIO()
    GeomTools_CurveSet.PrintCurve_s(value, stream, True)
    data = stream.getvalue()
    if not data:
        raise ValueError("OCCT produced an empty Curve serialization")
    return CurveValue(data)


def curve_to_ocp(value: CurveValue) -> Geom_Curve:
    if not isinstance(value, CurveValue):
        raise TypeError("curve_to_ocp expects CurveValue")
    curve = GeomTools_CurveSet.ReadCurve_s(BytesIO(value.data))
    if not isinstance(curve, Geom_Curve):
        raise ValueError("invalid OCCT Curve serialization")
    return curve


def curve2_from_ocp(value: Geom2d_Curve) -> Curve2Value:
    if not isinstance(value, Geom2d_Curve):
        raise TypeError("curve2_from_ocp expects Geom2d_Curve")
    stream = BytesIO()
    GeomTools_Curve2dSet.PrintCurve2d_s(value, stream, True)
    data = stream.getvalue()
    if not data:
        raise ValueError("OCCT produced an empty Curve2 serialization")
    return Curve2Value(data)


def curve2_to_ocp(value: Curve2Value) -> Geom2d_Curve:
    if not isinstance(value, Curve2Value):
        raise TypeError("curve2_to_ocp expects Curve2Value")
    curve = GeomTools_Curve2dSet.ReadCurve2d_s(BytesIO(value.data))
    if not isinstance(curve, Geom2d_Curve):
        raise ValueError("invalid OCCT Curve2 serialization")
    return curve


def valid_curve(value: CurveValue) -> bool:
    try:
        curve_to_ocp(value)
    except (TypeError, ValueError, RuntimeError):
        return False
    return True


def valid_curve2(value: Curve2Value) -> bool:
    try:
        curve2_to_ocp(value)
    except (TypeError, ValueError, RuntimeError):
        return False
    return True


def _point3(value: Point3Value) -> gp_Pnt:
    return gp_Pnt(value.x, value.y, value.z)


def _point2(value: Point2Value) -> gp_Pnt2d:
    return gp_Pnt2d(value.x, value.y)


def _positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive scalar")
    return value


def line(origin: Point3Value, direction: Vector3Value) -> CurveValue:
    length = math.sqrt(
        direction.x * direction.x
        + direction.y * direction.y
        + direction.z * direction.z
    )
    if not math.isfinite(length) or length == 0:
        raise ValueError("line direction must be a finite non-zero Vector3")
    native = Geom_Line(
        _point3(origin),
        gp_Dir(direction.x, direction.y, direction.z),
    )
    return curve_from_ocp(native)


def circle(radius: float) -> CurveValue:
    radius = _positive(radius, "circle radius")
    native = Geom_Circle(
        gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        radius,
    )
    return curve_from_ocp(native)


def ellipse(major_radius: float, minor_radius: float) -> CurveValue:
    major_radius = _positive(major_radius, "ellipse major radius")
    minor_radius = _positive(minor_radius, "ellipse minor radius")
    if major_radius < minor_radius:
        raise ValueError("ellipse major radius must not be less than minor radius")
    native = Geom_Ellipse(
        gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        major_radius,
        minor_radius,
    )
    return curve_from_ocp(native)


def curve_point(value: CurveValue, parameter: float) -> Point3Value:
    point = curve_to_ocp(value).Value(parameter)
    return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))


def curve_tangent(value: CurveValue, parameter: float) -> Vector3Value:
    point = gp_Pnt()
    tangent = gp_Vec()
    curve_to_ocp(value).D1(parameter, point, tangent)
    return Vector3Value(
        float(tangent.X()),
        float(tangent.Y()),
        float(tangent.Z()),
    )


def curve_first_parameter(value: CurveValue) -> float:
    return float(curve_to_ocp(value).FirstParameter())


def curve_last_parameter(value: CurveValue) -> float:
    return float(curve_to_ocp(value).LastParameter())


def segment2(start: Point2Value, end: Point2Value) -> Curve2Value:
    if start == end:
        raise ValueError("segment2 endpoints must be distinct")
    builder = GCE2d_MakeSegment(_point2(start), _point2(end))
    return curve2_from_ocp(builder.Value())


def ellipse2(major_radius: float, minor_radius: float) -> Curve2Value:
    major_radius = _positive(major_radius, "ellipse2 major radius")
    minor_radius = _positive(minor_radius, "ellipse2 minor radius")
    if major_radius < minor_radius:
        raise ValueError("ellipse2 major radius must not be less than minor radius")
    native = Geom2d_Ellipse(
        gp_Ax2d(gp_Pnt2d(0, 0), gp_Dir2d(1, 0)),
        major_radius,
        minor_radius,
    )
    return curve2_from_ocp(native)


def trim_curve2(
    value: Curve2Value,
    start: float,
    end: float,
) -> Curve2Value:
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError("trim_curve2 parameters must be finite")
    native = Geom2d_TrimmedCurve(curve2_to_ocp(value), start, end)
    return curve2_from_ocp(native)


def curve2_point(value: Curve2Value, parameter: float) -> Point2Value:
    point = curve2_to_ocp(value).Value(parameter)
    return Point2Value(float(point.X()), float(point.Y()))


def curve2_tangent(value: Curve2Value, parameter: float) -> Vector2Value:
    point = gp_Pnt2d()
    tangent = gp_Vec2d()
    curve2_to_ocp(value).D1(parameter, point, tangent)
    return Vector2Value(float(tangent.X()), float(tangent.Y()))


def curve2_first_parameter(value: Curve2Value) -> float:
    return float(curve2_to_ocp(value).FirstParameter())


def curve2_last_parameter(value: Curve2Value) -> float:
    return float(curve2_to_ocp(value).LastParameter())
