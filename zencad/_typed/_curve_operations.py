"""Resolved operations and immutable snapshots for typed curves."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math

from OCP.GCE2d import GCE2d_MakeSegment
from OCP.GCPnts import GCPnts_UniformAbscissa
from OCP.Geom import (
    Geom_BSplineCurve,
    Geom_BezierCurve,
    Geom_Circle,
    Geom_Curve,
    Geom_Ellipse,
    Geom_Line,
)
from OCP.GeomAPI import GeomAPI_Interpolate, GeomAPI_ProjectPointOnCurve
from OCP.GeomAbs import (
    GeomAbs_BSplineCurve,
    GeomAbs_BezierCurve,
    GeomAbs_Circle,
    GeomAbs_Ellipse,
    GeomAbs_Hyperbola,
    GeomAbs_Line,
    GeomAbs_OffsetCurve,
    GeomAbs_OtherCurve,
    GeomAbs_Parabola,
)
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.Geom2d import Geom2d_Curve, Geom2d_Ellipse, Geom2d_TrimmedCurve
from OCP.GeomTools import GeomTools_Curve2dSet, GeomTools_CurveSet
from OCP.TColStd import TColStd_HArray1OfBoolean
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

from zencad.opencascade_types import (
    opencascade_array1_of_int,
    opencascade_array1_of_pnt,
    opencascade_array1_of_real,
    opencascade_array1_of_vec,
    opencascade_h_array1_of_pnt,
)

from ._transform_operations import TransformValue, transform_to_ocp
from ._value_operations import (
    Point2Value,
    Point3Value,
    Vector2Value,
    Vector3Value,
)


@dataclass(frozen=True, slots=True)
class CurveValue:
    """Immutable full-precision OCCT snapshot of a three-dimensional curve."""

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes) or not self.data:
            raise TypeError("CurveValue data must be non-empty bytes")

    def __evalcache_key__(self) -> bytes:
        return b"zencad-curve-value-v2\x00" + self.data


@dataclass(frozen=True, slots=True)
class Curve2Value:
    """Immutable full-precision OCCT snapshot of a two-dimensional curve."""

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes) or not self.data:
            raise TypeError("Curve2Value data must be non-empty bytes")

    def __evalcache_key__(self) -> bytes:
        return b"zencad-curve2-value-v2\x00" + self.data


@dataclass(frozen=True, slots=True)
class LineParametersValue:
    origin: Point3Value
    direction: Vector3Value


@dataclass(frozen=True, slots=True)
class CircleParametersValue:
    center: Point3Value
    radius: float
    x_direction: Vector3Value
    y_direction: Vector3Value


@dataclass(frozen=True, slots=True)
class EllipseParametersValue:
    center: Point3Value
    major_radius: float
    minor_radius: float
    x_direction: Vector3Value
    y_direction: Vector3Value


def curve_from_ocp(value: Geom_Curve) -> CurveValue:
    if not isinstance(value, Geom_Curve):
        raise TypeError("curve_from_ocp expects Geom_Curve")
    curves = GeomTools_CurveSet()
    curves.Add(value)
    stream = BytesIO()
    curves.Write(stream)
    data = stream.getvalue()
    if not data:
        raise ValueError("OCCT produced an empty Curve serialization")
    return CurveValue(data)


def curve_to_ocp(value: CurveValue) -> Geom_Curve:
    if not isinstance(value, CurveValue):
        raise TypeError("curve_to_ocp expects CurveValue")
    curves = GeomTools_CurveSet()
    curves.Read(BytesIO(value.data))
    curve = curves.Curve(1)
    if not isinstance(curve, Geom_Curve):
        raise ValueError("invalid OCCT Curve serialization")
    return curve


def curve2_from_ocp(value: Geom2d_Curve) -> Curve2Value:
    if not isinstance(value, Geom2d_Curve):
        raise TypeError("curve2_from_ocp expects Geom2d_Curve")
    curves = GeomTools_Curve2dSet()
    curves.Add(value)
    stream = BytesIO()
    curves.Write(stream)
    data = stream.getvalue()
    if not data:
        raise ValueError("OCCT produced an empty Curve2 serialization")
    return Curve2Value(data)


def curve2_to_ocp(value: Curve2Value) -> Geom2d_Curve:
    if not isinstance(value, Curve2Value):
        raise TypeError("curve2_to_ocp expects Curve2Value")
    curves = GeomTools_Curve2dSet()
    curves.Read(BytesIO(value.data))
    curve = curves.Curve2d(1)
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


def interpolate(
    points: tuple[Point3Value, ...],
    tangents: tuple[Vector3Value | None, ...] | None,
    closed: bool,
) -> CurveValue:
    if len(points) < 2:
        raise ValueError("interpolate requires at least two points")
    native_points = opencascade_h_array1_of_pnt(
        tuple((point.x, point.y, point.z) for point in points)
    )
    algorithm = GeomAPI_Interpolate(native_points, closed, 1e-7)
    if tangents is not None:
        if len(tangents) != len(points):
            raise ValueError("interpolate tangents must match point count")
        native_tangents = opencascade_array1_of_vec(
            tuple(
                (0.0, 0.0, 0.0)
                if tangent is None
                else (tangent.x, tangent.y, tangent.z)
                for tangent in tangents
            )
        )
        tangent_flags = TColStd_HArray1OfBoolean(1, len(tangents))
        for index, tangent in enumerate(tangents, start=1):
            tangent_flags.SetValue(
                index,
                tangent is not None
                and (tangent.x != 0 or tangent.y != 0 or tangent.z != 0),
            )
        algorithm.Load(native_tangents, tangent_flags)
    algorithm.Perform()
    if not algorithm.IsDone():
        raise ValueError("curve interpolation failed")
    return curve_from_ocp(algorithm.Curve())


def bezier(
    poles: tuple[Point3Value, ...],
    weights: tuple[float, ...] | None,
) -> CurveValue:
    if len(poles) < 2:
        raise ValueError("bezier requires at least two poles")
    native_poles = opencascade_array1_of_pnt(
        tuple((pole.x, pole.y, pole.z) for pole in poles)
    )
    if weights is None:
        return curve_from_ocp(Geom_BezierCurve(native_poles))
    if len(weights) != len(poles):
        raise ValueError("bezier weights must match pole count")
    return curve_from_ocp(
        Geom_BezierCurve(native_poles, opencascade_array1_of_real(weights))
    )


def bspline(
    poles: tuple[Point3Value, ...],
    knots: tuple[float, ...],
    multiplicities: tuple[int, ...],
    degree: int,
    periodic: bool,
    weights: tuple[float, ...] | None,
    check_rational: bool | None,
) -> CurveValue:
    if len(poles) < 2:
        raise ValueError("bspline requires at least two poles")
    if len(knots) != len(multiplicities):
        raise ValueError("bspline knots and multiplicities must have equal length")
    if isinstance(degree, bool) or not isinstance(degree, int) or degree < 1:
        raise ValueError("bspline degree must be a positive int")
    native_poles = opencascade_array1_of_pnt(
        tuple((pole.x, pole.y, pole.z) for pole in poles)
    )
    native_knots = opencascade_array1_of_real(knots)
    native_multiplicities = opencascade_array1_of_int(multiplicities)
    if weights is None:
        native = Geom_BSplineCurve(
            native_poles,
            native_knots,
            native_multiplicities,
            degree,
            periodic,
        )
    else:
        if len(weights) != len(poles):
            raise ValueError("bspline weights must match pole count")
        native = Geom_BSplineCurve(
            native_poles,
            opencascade_array1_of_real(weights),
            native_knots,
            native_multiplicities,
            degree,
            periodic,
            True if check_rational is None else check_rational,
        )
    return curve_from_ocp(native)


def curve_transform(value: CurveValue, transform: TransformValue) -> CurveValue:
    return curve_from_ocp(curve_to_ocp(value).Transformed(transform_to_ocp(transform)))


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


_CURVE_KIND_NAMES = {
    GeomAbs_Line: "line",
    GeomAbs_Circle: "circle",
    GeomAbs_Ellipse: "ellipse",
    GeomAbs_Hyperbola: "hyperbola",
    GeomAbs_Parabola: "parabola",
    GeomAbs_BezierCurve: "bezier",
    GeomAbs_BSplineCurve: "bspline",
    GeomAbs_OffsetCurve: "offset",
    GeomAbs_OtherCurve: "other",
}


def _curve_adaptor(value: CurveValue) -> GeomAdaptor_Curve:
    return GeomAdaptor_Curve(curve_to_ocp(value))


def curve_kind(value: CurveValue) -> str:
    try:
        return _CURVE_KIND_NAMES[_curve_adaptor(value).GetType()]
    except KeyError as exception:
        raise ValueError("unsupported curve kind") from exception


def _point3_value(point: gp_Pnt) -> Point3Value:
    return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))


def _vector3_value(vector: gp_Vec | gp_Dir) -> Vector3Value:
    return Vector3Value(float(vector.X()), float(vector.Y()), float(vector.Z()))


def curve_line_parameters(value: CurveValue) -> LineParametersValue:
    adaptor = _curve_adaptor(value)
    if adaptor.GetType() != GeomAbs_Line:
        raise TypeError("curve is not a line")
    line_value = adaptor.Line()
    return LineParametersValue(
        _point3_value(line_value.Location()),
        _vector3_value(line_value.Direction()),
    )


def curve_circle_parameters(value: CurveValue) -> CircleParametersValue:
    adaptor = _curve_adaptor(value)
    if adaptor.GetType() != GeomAbs_Circle:
        raise TypeError("curve is not a circle")
    circle_value = adaptor.Circle()
    position = circle_value.Position()
    return CircleParametersValue(
        _point3_value(position.Location()),
        float(circle_value.Radius()),
        _vector3_value(position.XDirection()),
        _vector3_value(position.YDirection()),
    )


def curve_ellipse_parameters(value: CurveValue) -> EllipseParametersValue:
    adaptor = _curve_adaptor(value)
    if adaptor.GetType() != GeomAbs_Ellipse:
        raise TypeError("curve is not an ellipse")
    ellipse_value = adaptor.Ellipse()
    position = ellipse_value.Position()
    return EllipseParametersValue(
        _point3_value(position.Location()),
        float(ellipse_value.MajorRadius()),
        float(ellipse_value.MinorRadius()),
        _vector3_value(position.XDirection()),
        _vector3_value(position.YDirection()),
    )


def line_parameters_origin(value: LineParametersValue) -> Point3Value:
    return value.origin


def line_parameters_direction(value: LineParametersValue) -> Vector3Value:
    return value.direction


def circle_parameters_center(value: CircleParametersValue) -> Point3Value:
    return value.center


def circle_parameters_radius(value: CircleParametersValue) -> float:
    return value.radius


def circle_parameters_x_direction(value: CircleParametersValue) -> Vector3Value:
    return value.x_direction


def circle_parameters_y_direction(value: CircleParametersValue) -> Vector3Value:
    return value.y_direction


def ellipse_parameters_center(value: EllipseParametersValue) -> Point3Value:
    return value.center


def ellipse_parameters_major_radius(value: EllipseParametersValue) -> float:
    return value.major_radius


def ellipse_parameters_minor_radius(value: EllipseParametersValue) -> float:
    return value.minor_radius


def ellipse_parameters_x_direction(value: EllipseParametersValue) -> Vector3Value:
    return value.x_direction


def ellipse_parameters_y_direction(value: EllipseParametersValue) -> Vector3Value:
    return value.y_direction


def curve_lower_distance_parameter(value: CurveValue, point: Point3Value) -> float:
    projector = GeomAPI_ProjectPointOnCurve(_point3(point), curve_to_ocp(value))
    if projector.NbPoints() == 0:
        raise ValueError("point projection onto curve failed")
    return float(projector.LowerDistanceParameter())


def curve_uniform_parameters(
    value: CurveValue,
    count: int,
    start: float | None,
    end: float | None,
) -> tuple[float, ...]:
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("uniform sample count must be a positive int")
    adaptor = _curve_adaptor(value)
    if start is None and end is None:
        start = float(adaptor.FirstParameter())
        end = float(adaptor.LastParameter())
    elif start is None or end is None:
        raise TypeError("uniform start and end must be provided together")
    algorithm = GCPnts_UniformAbscissa(adaptor, count, start, end)
    if not algorithm.IsDone():
        raise ValueError("uniform curve sampling failed")
    return tuple(float(algorithm.Parameter(index + 1)) for index in range(count))


def scalar_sequence_item(values: tuple[float, ...], index: int) -> float:
    return values[index]


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
