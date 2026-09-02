"""Typed curve and wire constructors declared as module-level operations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from zencad.operation import operation

from . import _curve_operations as curve_ops
from . import _operations as topology_ops
from .curves import CURVE2_SPEC, CURVE_SPEC, Curve, Curve2
from .records import Interval
from .topology import EDGE_SPEC, WIRE_SPEC, Edge, Wire
from .transforms import Transform
from .values import Point2, Point3, Point3Input, Vector3, Vector3Input


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.line",
    operation_version="1",
)
def line(origin: Point3Input, direction: Vector3Input, /) -> Curve:
    if not isinstance(origin, Point3):
        raise TypeError("line origin must be Point3")
    if not isinstance(direction, Vector3):
        raise TypeError("line direction must be Vector3")
    return Curve(curve_ops.line(origin._resolved(), direction._resolved()))


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.circle_curve",
    operation_version="1",
)
def circle_curve(radius: float, /) -> Curve:
    return Curve(curve_ops.circle(radius))


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.ellipse_curve",
    operation_version="1",
)
def ellipse_curve(
    major_radius: float,
    minor_radius: float,
    /,
) -> Curve:
    return Curve(curve_ops.ellipse(major_radius, minor_radius))


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.interpolate_curve",
    operation_version="1",
)
def interpolate_curve(
    pnts: Sequence[Point3Input],
    tangs: Sequence[Vector3Input | None] | None = None,
    closed: bool = False,
) -> Curve:
    _require_bool(closed, "interpolate_curve closed")
    points = _require_points(pnts, minimum=2, name="interpolate_curve")
    tangents = _require_tangents(tangs, len(points), "interpolate_curve")
    return Curve(
        curve_ops.interpolate(
            tuple(point._resolved() for point in points),
            None
            if tangents is None
            else tuple(
                None if tangent is None else tangent._resolved() for tangent in tangents
            ),
            closed,
        )
    )


def interpolate(
    pnts: Sequence[Point3Input],
    tangs: Sequence[Vector3Input | None] | None = None,
    closed: bool = False,
) -> Edge:
    """Compatibility edge alias for :func:`interpolate_curve`."""

    return interpolate_curve(pnts, tangs, closed).edge()


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.bezier_curve",
    operation_version="1",
)
def bezier_curve(
    poles: Sequence[Point3Input],
    weights: Sequence[float] | None = None,
) -> Curve:
    points = _require_points(poles, minimum=2, name="bezier_curve")
    resolved_weights = _optional_scalar_sequence(weights, "bezier_curve weights")
    return Curve(
        curve_ops.bezier(
            tuple(point._resolved() for point in points),
            resolved_weights,
        )
    )


def bezier(
    pnts: Sequence[Point3Input],
    weights: Sequence[float] | None = None,
) -> Edge:
    """Compatibility edge alias for :func:`bezier_curve`."""

    return bezier_curve(pnts, weights).edge()


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.bspline_curve",
    operation_version="1",
)
def bspline_curve(
    poles: Sequence[Point3Input],
    knots: Sequence[float],
    muls: Sequence[int],
    degree: int,
    periodic: bool = False,
    weights: Sequence[float] | None = None,
    check_rational: bool | None = None,
) -> Curve:
    points = _require_points(poles, minimum=2, name="bspline_curve")
    if isinstance(degree, bool) or not isinstance(degree, int) or degree < 1:
        raise ValueError("bspline_curve degree must be a positive int")
    _require_bool(periodic, "bspline_curve periodic")
    if check_rational is not None:
        _require_bool(check_rational, "bspline_curve check_rational")
    knot_values = _scalar_sequence(knots, "bspline_curve knots")
    multiplicities = _int_sequence(muls, "bspline_curve multiplicities")
    if len(knot_values) != len(multiplicities):
        raise ValueError(
            "bspline_curve knots and multiplicities must have equal length"
        )
    resolved_weights = _optional_scalar_sequence(weights, "bspline_curve weights")
    return Curve(
        curve_ops.bspline(
            tuple(point._resolved() for point in points),
            knot_values,
            multiplicities,
            degree,
            periodic,
            resolved_weights,
            check_rational,
        )
    )


def bspline(
    poles: Sequence[Point3Input],
    knots: Sequence[float],
    muls: Sequence[int],
    degree: int,
    periodic: bool = False,
    weights: Sequence[float] | None = None,
    check_rational: bool | None = None,
) -> Edge:
    """Compatibility edge alias for :func:`bspline_curve`."""

    return bspline_curve(
        poles,
        knots,
        muls,
        degree,
        periodic,
        weights,
        check_rational,
    ).edge()


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.make_edge",
    operation_version="1",
)
def make_edge(
    curve: Curve,
    interval: Interval | Sequence[float] | None = None,
    /,
) -> Edge:
    if not isinstance(curve, Curve):
        raise TypeError("make_edge expects Curve")
    return Edge(
        topology_ops.curve_edge(
            curve._resolved(),
            _interval_values(interval, "make_edge interval"),
        )
    )


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.circle_arc",
    operation_version="1",
)
def circle_arc(p1: Point3Input, p2: Point3Input, p3: Point3Input, /) -> Edge:
    points = _require_points((p1, p2, p3), minimum=3, name="circle_arc")
    return Edge(topology_ops.circle_arc(*(point._resolved() for point in points)))


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.svg_elliptic_arc",
    operation_version="1",
)
def _svg_elliptic_arc(
    start: Point3,
    end: Point3,
    radius_x: float,
    radius_y: float,
    x_axis_angle: float,
    large: bool,
    sweep: bool,
) -> Edge:
    points = _require_points((start, end), minimum=2, name="SVG arc")
    _require_bool(large, "SVG arc large")
    _require_bool(sweep, "SVG arc sweep")
    return Edge(
        topology_ops.svg_elliptic_arc(
            points[0]._resolved(),
            points[1]._resolved(),
            radius_x,
            radius_y,
            x_axis_angle,
            large,
            sweep,
        )
    )


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.make_wire",
    operation_version="1",
)
def make_wire(*shapes: Edge | Wire | Sequence[Edge | Wire]) -> Wire:
    parts = _require_wire_parts(shapes, "make_wire")
    return Wire(topology_ops.make_wire(tuple(part._legacy() for part in parts)))


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.rounded_polysegment",
    operation_version="1",
)
def rounded_polysegment(
    pnts: Sequence[Point3Input],
    r: float,
    closed: bool = False,
) -> Wire:
    _require_bool(closed, "rounded_polysegment closed")
    points = _require_points(pnts, minimum=2, name="rounded_polysegment")
    return Wire(
        topology_ops.rounded_polysegment(
            tuple(point._resolved() for point in points), r, closed
        )
    )


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.helix",
    operation_version="1",
)
def helix(
    r: float,
    h: float,
    step: float | None = None,
    pitch: float | None = None,
    angle: float = 0,
    left: bool = False,
) -> Wire:
    if step is None and pitch is None:
        raise TypeError("helix requires step or pitch")
    _require_bool(left, "helix left")
    return Wire(topology_ops.helix(r, h, step, pitch, angle, left))


@operation(
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.segment2",
    operation_version="1",
)
def segment2(start: Point2, end: Point2, /) -> Curve2:
    if not isinstance(start, Point2) or not isinstance(end, Point2):
        raise TypeError("segment2 expects Point2 endpoints")
    return Curve2(curve_ops.segment2(start._resolved(), end._resolved()))


@operation(
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.ellipse2",
    operation_version="1",
)
def ellipse2(
    major_radius: float,
    minor_radius: float,
    /,
) -> Curve2:
    return Curve2(curve_ops.ellipse2(major_radius, minor_radius))


@operation(
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.trim_curve2",
    operation_version="1",
)
def trim_curve2(
    curve: Curve2,
    start: float,
    end: float,
    /,
) -> Curve2:
    if not isinstance(curve, Curve2):
        raise TypeError("trim_curve2 expects Curve2")
    return Curve2(curve_ops.trim_curve2(curve._resolved(), start, end))


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.segment",
    operation_version="1",
)
def segment(start: Point3Input, end: Point3Input, /) -> Edge:
    points = _require_points((start, end), minimum=2, name="segment")
    return Edge(topology_ops.segment(*(point._resolved() for point in points)))


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.polysegment",
    operation_version="1",
)
def polysegment(
    points: Sequence[Point3Input],
    /,
    *,
    closed: bool = False,
) -> Wire:
    _require_bool(closed, "polysegment closed")
    values = _require_points(points, minimum=2, name="polysegment")
    return Wire(
        topology_ops.polysegment(tuple(point._resolved() for point in values), closed)
    )


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.curve.trimmed_edge",
    operation_version="1",
)
def _curve_trimmed_edge(
    curve: Curve,
    start: float,
    end: float,
    /,
) -> Edge:
    return Edge(topology_ops.curve_trimmed_edge(curve._resolved(), start, end))


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.curve.transform",
    operation_version="1",
)
def _curve_transform(curve: Curve, transformation: Transform, /) -> Curve:
    if not isinstance(transformation, Transform):
        raise TypeError("Curve.transform expects Transform")
    return Curve(
        curve_ops.curve_transform(curve._resolved(), transformation._resolved())
    )


@operation(
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.curve2.rotate",
    operation_version="1",
)
def _curve2_rotate(
    curve: Curve2,
    angle: float,
    /,
) -> Curve2:
    return Curve2(curve_ops.curve2_rotate(curve._resolved(), angle))


@operation(
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.edge.curve",
    operation_version="1",
    fold_literals=True,
)
def _edge_curve(edge: Edge, /) -> Curve:
    return Curve(topology_ops.edge_curve(edge._legacy()))


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_points(
    points: Sequence[Point3Input],
    *,
    minimum: int,
    name: str,
) -> tuple[Point3, ...]:
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise TypeError(f"{name} expects a sequence of Point3")
    values = tuple(points)
    if len(values) < minimum:
        raise ValueError(f"{name} requires at least {minimum} points")
    if not all(isinstance(point, Point3) for point in values):
        raise TypeError(f"{name} expects only Point3 values")
    return values


def _require_tangents(
    tangents: Sequence[Vector3Input | None] | None,
    point_count: int,
    name: str,
) -> tuple[Vector3 | None, ...] | None:
    if tangents is None:
        return None
    if isinstance(tangents, (str, bytes)) or not isinstance(tangents, Sequence):
        raise TypeError(f"{name} tangents must be a sequence")
    values = tuple(tangents)
    if len(values) != point_count:
        raise ValueError(f"{name} tangents must match point count")
    if not all(tangent is None or isinstance(tangent, Vector3) for tangent in values):
        raise TypeError(f"{name} tangents must contain only Vector3 or None")
    return values


def _scalar_sequence(
    values: Sequence[float],
    name: str,
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a scalar sequence")
    result = tuple(values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _optional_scalar_sequence(
    values: Sequence[float] | None,
    name: str,
) -> tuple[float, ...] | None:
    if values is None:
        return None
    return _scalar_sequence(values, name)


def _int_sequence(values: Sequence[int], name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be an int sequence")
    result = tuple(values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    if not all(
        isinstance(value, int) and not isinstance(value, bool) for value in result
    ):
        raise TypeError(f"{name} must contain only int values")
    return result


def _interval_values(
    interval: Interval | Sequence[float] | None,
    name: str,
) -> tuple[float, float] | None:
    if interval is None:
        return None
    if isinstance(interval, Interval):
        return (interval.lower.value(), interval.upper.value())
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence):
        raise TypeError(f"{name} must contain two scalar bounds")
    values = tuple(interval)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    return (values[0], values[1])


def _require_wire_parts(
    shapes: tuple[Edge | Wire | Sequence[Edge | Wire], ...],
    name: str,
) -> tuple[Edge | Wire, ...]:
    if len(shapes) == 1 and isinstance(shapes[0], Sequence):
        candidate = shapes[0]
        if isinstance(candidate, (str, bytes)):
            raise TypeError(f"{name} expects Edge or Wire handles")
        values = tuple(candidate)
    else:
        values = cast(tuple[Edge | Wire, ...], shapes)
    if not values:
        raise ValueError(f"{name} requires at least one Edge or Wire")
    if not all(isinstance(shape, (Edge, Wire)) for shape in values):
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    return values


__all__ = [
    "bezier",
    "bezier_curve",
    "bspline",
    "bspline_curve",
    "circle_arc",
    "circle_curve",
    "ellipse2",
    "ellipse_curve",
    "helix",
    "interpolate",
    "interpolate_curve",
    "line",
    "make_edge",
    "make_wire",
    "polysegment",
    "rounded_polysegment",
    "segment",
    "segment2",
    "trim_curve2",
]
