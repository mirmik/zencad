"""Typed curve and wire constructors declared as module-level operations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from zencad.operation import OperationArguments, arguments, operation, resolve_runtime

from . import _curve_operations as curve_ops
from . import _operations as topology_ops
from .curves import CURVE2_SPEC, CURVE_SPEC, Curve, Curve2
from .records import Interval
from .topology import EDGE_SPEC, WIRE_SPEC, Edge, Wire
from .transforms import Transform
from .values import (
    Point2,
    Point3,
    ScalarInput,
    Vector3,
    _optional_scalar_state,
    _scalar_state,
)

if TYPE_CHECKING:
    from .runtime import Runtime


@operation(
    backend=curve_ops.line,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.line",
    operation_version="1",
)
def line(origin: Point3, direction: Vector3, /) -> OperationArguments:
    if not isinstance(origin, Point3):
        raise TypeError("line origin must be Point3")
    if not isinstance(direction, Vector3):
        raise TypeError("line direction must be Vector3")
    return arguments(origin, direction)


@operation(
    backend=curve_ops.circle,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.circle_curve",
    operation_version="1",
)
def circle_curve(radius: ScalarInput, /) -> OperationArguments:
    runtime = resolve_runtime(radius)
    return arguments(_scalar_state(runtime, radius))


@operation(
    backend=curve_ops.ellipse,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.ellipse_curve",
    operation_version="1",
)
def ellipse_curve(
    major_radius: ScalarInput,
    minor_radius: ScalarInput,
    /,
) -> OperationArguments:
    runtime = resolve_runtime(major_radius, minor_radius)
    return arguments(
        _scalar_state(runtime, major_radius),
        _scalar_state(runtime, minor_radius),
    )


@operation(
    backend=curve_ops.interpolate,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.interpolate_curve",
    operation_version="1",
)
def interpolate_curve(
    pnts: Sequence[Point3],
    tangs: Sequence[Vector3 | None] | None = None,
    closed: bool = False,
) -> OperationArguments:
    _require_bool(closed, "interpolate_curve closed")
    points = _require_points(pnts, minimum=2, name="interpolate_curve")
    tangents = _require_tangents(tangs, len(points), "interpolate_curve")
    return arguments(points, tangents, closed)


def interpolate(
    pnts: Sequence[Point3],
    tangs: Sequence[Vector3 | None] | None = None,
    closed: bool = False,
) -> Edge:
    """Compatibility edge alias for :func:`interpolate_curve`."""

    return interpolate_curve(pnts, tangs, closed).edge()


@operation(
    backend=curve_ops.bezier,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.bezier_curve",
    operation_version="1",
)
def bezier_curve(
    poles: Sequence[Point3],
    weights: Sequence[ScalarInput] | None = None,
) -> OperationArguments:
    points = _require_points(poles, minimum=2, name="bezier_curve")
    runtime = resolve_runtime(points, weights)
    resolved_weights = _optional_scalar_sequence_state(
        runtime,
        weights,
        "bezier_curve weights",
    )
    return arguments(points, resolved_weights)


def bezier(
    pnts: Sequence[Point3],
    weights: Sequence[ScalarInput] | None = None,
) -> Edge:
    """Compatibility edge alias for :func:`bezier_curve`."""

    return bezier_curve(pnts, weights).edge()


@operation(
    backend=curve_ops.bspline,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.bspline_curve",
    operation_version="1",
)
def bspline_curve(
    poles: Sequence[Point3],
    knots: Sequence[ScalarInput],
    muls: Sequence[int],
    degree: int,
    periodic: bool = False,
    weights: Sequence[ScalarInput] | None = None,
    check_rational: bool | None = None,
) -> OperationArguments:
    points = _require_points(poles, minimum=2, name="bspline_curve")
    if isinstance(degree, bool) or not isinstance(degree, int) or degree < 1:
        raise ValueError("bspline_curve degree must be a positive int")
    _require_bool(periodic, "bspline_curve periodic")
    if check_rational is not None:
        _require_bool(check_rational, "bspline_curve check_rational")
    runtime = resolve_runtime(points, knots, weights)
    knot_states = _scalar_sequence_state(runtime, knots, "bspline_curve knots")
    multiplicities = _int_sequence(muls, "bspline_curve multiplicities")
    if len(knot_states) != len(multiplicities):
        raise ValueError("bspline_curve knots and multiplicities must have equal length")
    resolved_weights = _optional_scalar_sequence_state(
        runtime,
        weights,
        "bspline_curve weights",
    )
    return arguments(
        points,
        knot_states,
        multiplicities,
        degree,
        periodic,
        resolved_weights,
        check_rational,
    )


def bspline(
    poles: Sequence[Point3],
    knots: Sequence[ScalarInput],
    muls: Sequence[int],
    degree: int,
    periodic: bool = False,
    weights: Sequence[ScalarInput] | None = None,
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
    backend=topology_ops.curve_edge,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.make_edge",
    operation_version="1",
)
def make_edge(
    curve: Curve,
    interval: Interval | Sequence[ScalarInput] | None = None,
    /,
) -> OperationArguments:
    if not isinstance(curve, Curve):
        raise TypeError("make_edge expects Curve")
    runtime = resolve_runtime(curve)
    return arguments(curve, _interval_state(runtime, interval, "make_edge interval"))


@operation(
    backend=topology_ops.circle_arc,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.circle_arc",
    operation_version="1",
)
def circle_arc(p1: Point3, p2: Point3, p3: Point3, /) -> OperationArguments:
    points = _require_points((p1, p2, p3), minimum=3, name="circle_arc")
    return arguments(*points)


@operation(
    backend=topology_ops.svg_elliptic_arc,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.svg_elliptic_arc",
    operation_version="1",
)
def _svg_elliptic_arc(
    start: Point3,
    end: Point3,
    radius_x: ScalarInput,
    radius_y: ScalarInput,
    x_axis_angle: ScalarInput,
    large: bool,
    sweep: bool,
) -> OperationArguments:
    points = _require_points((start, end), minimum=2, name="SVG arc")
    _require_bool(large, "SVG arc large")
    _require_bool(sweep, "SVG arc sweep")
    runtime = resolve_runtime(points, radius_x, radius_y, x_axis_angle)
    return arguments(
        points[0],
        points[1],
        _scalar_state(runtime, radius_x),
        _scalar_state(runtime, radius_y),
        _scalar_state(runtime, x_axis_angle),
        large,
        sweep,
    )


@operation(
    backend=topology_ops.make_wire,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.make_wire",
    operation_version="1",
)
def make_wire(*shapes: Edge | Wire | Sequence[Edge | Wire]) -> OperationArguments:
    return arguments(_require_wire_parts(shapes, "make_wire"))


@operation(
    backend=topology_ops.rounded_polysegment,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.rounded_polysegment",
    operation_version="1",
)
def rounded_polysegment(
    pnts: Sequence[Point3],
    r: ScalarInput,
    closed: bool = False,
) -> OperationArguments:
    _require_bool(closed, "rounded_polysegment closed")
    points = _require_points(pnts, minimum=2, name="rounded_polysegment")
    runtime = resolve_runtime(points, r)
    return arguments(points, _scalar_state(runtime, r), closed)


@operation(
    backend=topology_ops.helix,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.helix",
    operation_version="1",
)
def helix(
    r: ScalarInput,
    h: ScalarInput,
    step: ScalarInput | None = None,
    pitch: ScalarInput | None = None,
    angle: ScalarInput = 0,
    left: bool = False,
) -> OperationArguments:
    if step is None and pitch is None:
        raise TypeError("helix requires step or pitch")
    _require_bool(left, "helix left")
    runtime = resolve_runtime(r, h, step, pitch, angle)
    return arguments(
        _scalar_state(runtime, r),
        _scalar_state(runtime, h),
        _optional_scalar_state(runtime, step),
        _optional_scalar_state(runtime, pitch),
        _scalar_state(runtime, angle),
        left,
    )


@operation(
    backend=curve_ops.segment2,
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.segment2",
    operation_version="1",
)
def segment2(start: Point2, end: Point2, /) -> OperationArguments:
    if not isinstance(start, Point2) or not isinstance(end, Point2):
        raise TypeError("segment2 expects Point2 endpoints")
    return arguments(start, end)


@operation(
    backend=curve_ops.ellipse2,
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.ellipse2",
    operation_version="1",
)
def ellipse2(
    major_radius: ScalarInput,
    minor_radius: ScalarInput,
    /,
) -> OperationArguments:
    runtime = resolve_runtime(major_radius, minor_radius)
    return arguments(
        _scalar_state(runtime, major_radius),
        _scalar_state(runtime, minor_radius),
    )


@operation(
    backend=curve_ops.trim_curve2,
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.trim_curve2",
    operation_version="1",
)
def trim_curve2(
    curve: Curve2,
    start: ScalarInput,
    end: ScalarInput,
    /,
) -> OperationArguments:
    if not isinstance(curve, Curve2):
        raise TypeError("trim_curve2 expects Curve2")
    runtime = resolve_runtime(curve, start, end)
    return arguments(
        curve,
        _scalar_state(runtime, start),
        _scalar_state(runtime, end),
    )


@operation(
    backend=topology_ops.segment,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.segment",
    operation_version="1",
)
def segment(start: Point3, end: Point3, /) -> OperationArguments:
    points = _require_points((start, end), minimum=2, name="segment")
    return arguments(*points)


@operation(
    backend=topology_ops.polysegment,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.polysegment",
    operation_version="1",
)
def polysegment(
    points: Sequence[Point3],
    /,
    *,
    closed: bool = False,
) -> OperationArguments:
    _require_bool(closed, "polysegment closed")
    values = _require_points(points, minimum=2, name="polysegment")
    return arguments(values, closed)


@operation(
    backend=topology_ops.curve_trimmed_edge,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.curve.trimmed_edge",
    operation_version="1",
)
def _curve_trimmed_edge(
    curve: Curve,
    start: ScalarInput,
    end: ScalarInput,
    /,
) -> OperationArguments:
    runtime = resolve_runtime(curve, start, end)
    return arguments(
        curve,
        _scalar_state(runtime, start),
        _scalar_state(runtime, end),
    )


@operation(
    backend=curve_ops.curve_transform,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.curve.transform",
    operation_version="1",
)
def _curve_transform(curve: Curve, transformation: Transform, /) -> OperationArguments:
    if not isinstance(transformation, Transform):
        raise TypeError("Curve.transform expects Transform")
    return arguments(curve, transformation)


@operation(
    backend=curve_ops.curve2_rotate,
    result=CURVE2_SPEC,
    returns=Curve2,
    operation_id="zencad.typed.curve2.rotate",
    operation_version="1",
)
def _curve2_rotate(
    curve: Curve2,
    angle: ScalarInput,
    /,
) -> OperationArguments:
    runtime = resolve_runtime(curve, angle)
    return arguments(curve, _scalar_state(runtime, angle))


@operation(
    backend=topology_ops.edge_curve,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.edge.curve",
    operation_version="1",
    fold_literals=True,
)
def _edge_curve(edge: Edge, /) -> OperationArguments:
    return arguments(edge)


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_points(
    points: Sequence[Point3],
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
    tangents: Sequence[Vector3 | None] | None,
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


def _scalar_sequence_state(
    runtime: Runtime,
    values: Sequence[ScalarInput],
    name: str,
) -> tuple[object, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a scalar sequence")
    result = tuple(_scalar_state(runtime, value) for value in values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _optional_scalar_sequence_state(
    runtime: Runtime,
    values: Sequence[ScalarInput] | None,
    name: str,
) -> tuple[object, ...] | None:
    if values is None:
        return None
    return _scalar_sequence_state(runtime, values, name)


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


def _interval_state(
    runtime: Runtime,
    interval: Interval | Sequence[ScalarInput] | None,
    name: str,
) -> tuple[object, object] | None:
    if interval is None:
        return None
    if isinstance(interval, Interval):
        return (interval.lower, interval.upper)
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence):
        raise TypeError(f"{name} must contain two scalar bounds")
    values = tuple(interval)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    return (_scalar_state(runtime, values[0]), _scalar_state(runtime, values[1]))


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
