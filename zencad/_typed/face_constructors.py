"""Typed planar face constructors declared at module level."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Literal, overload

from evalcache import ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.operation import (
    operation,
    resolve_context,
    using_context,
)

from . import _operations as ops
from .curve_constructors import polysegment
from .topology import (
    EDGE_SPEC,
    FACE_SPEC,
    SHAPE_SPEC,
    Edge,
    Face,
    Shape,
    Wire,
)
from .values import (
    Point3,
    Scalar,
    point3,
    scalar,
)


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _angle_values(
    value: float | Sequence[float] | None,
    name: str,
) -> float | tuple[float, float] | None:
    if value is None or isinstance(value, (int, float)):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values = tuple(value)
        if len(values) != 2:
            raise TypeError(f"{name} must contain exactly two scalar bounds")
        return values
    raise TypeError(f"{name} must be a scalar or two scalar bounds")


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


def _require_wire_parts(
    shapes: Edge | Wire | Sequence[Edge | Wire],
    name: str,
) -> tuple[Edge | Wire, ...]:
    if isinstance(shapes, (Edge, Wire)):
        values = (shapes,)
    elif isinstance(shapes, Sequence) and not isinstance(shapes, (str, bytes)):
        values = tuple(shapes)
    else:
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    if not values:
        raise ValueError(f"{name} requires at least one Edge or Wire")
    if not all(isinstance(shape, (Edge, Wire)) for shape in values):
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    return values


def _as_scalar(value: float | Scalar) -> Scalar:
    if isinstance(value, Scalar):
        return value
    return scalar(value)


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.polygon",
    operation_version="1",
)
def _polygon_face(points: Sequence[Point3], /) -> Face:
    values = _require_points(points, minimum=3, name="polygon")
    return Face(ops.polygon(tuple(point._resolved() for point in values)))


@overload
def polygon(points: Sequence[Point3], wire: Literal[False] = False) -> Face: ...


@overload
def polygon(points: Sequence[Point3], wire: Literal[True]) -> Wire: ...


@overload
def polygon(points: Sequence[Point3], wire: bool) -> Face | Wire: ...


def polygon(
    points: Sequence[Point3],
    wire: bool = False,
) -> Face | Wire:
    _require_bool(wire, "polygon wire")
    values = _require_points(points, minimum=3, name="polygon")
    if wire:
        return polysegment(values, closed=True)
    return _polygon_face(values)


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.rectangle",
    operation_version="1",
)
def _rectangle_face(
    width: float,
    height: float,
    center: bool,
    /,
) -> Face:
    _require_bool(center, "rectangle center")
    return Face(ops.rectangle(width, height, center))


def rectangle_wire(
    a: float,
    b: float,
    center: bool = False,
) -> Wire:
    _require_bool(center, "rectangle_wire center")
    context = resolve_context(a, b)
    with using_context(context):
        width = _as_scalar(a)
        height = _as_scalar(b)
        x0 = -width / 2 if center else scalar(0)
        y0 = -height / 2 if center else scalar(0)
        return polysegment(
            (
                point3(x0, y0, 0),
                point3(x0 + width, y0, 0),
                point3(x0 + width, y0 + height, 0),
                point3(x0, y0 + height, 0),
            ),
            closed=True,
        )


@overload
def rectangle(
    a: float,
    b: float | None = None,
    center: bool = False,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def rectangle(
    a: float,
    b: float | None = None,
    center: bool = False,
    *,
    wire: Literal[True],
) -> Wire: ...


@overload
def rectangle(
    a: float,
    b: float | None,
    center: bool,
    wire: Literal[True],
) -> Wire: ...


@overload
def rectangle(
    a: float,
    b: float | None,
    center: bool,
    wire: bool,
) -> Face | Wire: ...


def rectangle(
    a: float,
    b: float | None = None,
    center: bool = False,
    wire: bool = False,
) -> Face | Wire:
    _require_bool(center, "rectangle center")
    _require_bool(wire, "rectangle wire")
    resolved_height = a if b is None else b
    if wire:
        return rectangle_wire(a, resolved_height, center)
    return _rectangle_face(a, resolved_height, center)


@overload
def square(
    a: float,
    b: float | None = None,
    center: bool = False,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def square(
    a: float,
    b: float | None = None,
    center: bool = False,
    *,
    wire: Literal[True],
) -> Wire: ...


@overload
def square(
    a: float,
    b: float | None,
    center: bool,
    wire: Literal[True],
) -> Wire: ...


@overload
def square(
    a: float,
    b: float | None,
    center: bool,
    wire: bool,
) -> Face | Wire: ...


def square(
    a: float,
    b: float | None = None,
    center: bool = False,
    wire: bool = False,
) -> Face | Wire:
    return rectangle(a, b, center, wire)


@overload
def ngon(r: float, n: int, wire: Literal[False] = False) -> Face: ...


@overload
def ngon(r: float, n: int, wire: Literal[True]) -> Wire: ...


@overload
def ngon(r: float, n: int, wire: bool) -> Face | Wire: ...


def ngon(
    r: float,
    n: int,
    wire: bool = False,
) -> Face | Wire:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("ngon n must be int")
    if n < 3:
        raise ValueError("ngon n must be at least 3")
    _require_bool(wire, "ngon wire")
    context = resolve_context(r)
    with using_context(context):
        radius = _as_scalar(r)
        points = tuple(
            point3(
                radius * math.cos(2 * math.pi * index / n),
                radius * math.sin(2 * math.pi * index / n),
                0,
            )
            for index in range(n)
        )
        return polygon(points, wire)


def _wire_argument(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    position: int,
) -> bool:
    value = args[position] if len(args) > position else kwargs.get("wire", False)
    return value is True


def _circle_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Face | Edge]:
    return Edge if _wire_argument(args, kwargs, 2) else Face


def _circle_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    return EDGE_SPEC if _wire_argument(args, kwargs, 2) else FACE_SPEC


@overload
def circle(
    r: float,
    angle: float | Sequence[float] | None = None,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def circle(
    r: float,
    angle: float | Sequence[float] | None = None,
    *,
    wire: Literal[True],
) -> Edge: ...


@overload
def circle(
    r: float,
    angle: float | Sequence[float] | None,
    wire: Literal[True],
) -> Edge: ...


@overload
def circle(
    r: float,
    angle: float | Sequence[float] | None,
    wire: bool,
) -> Face | Edge: ...


@operation(
    result=FACE_SPEC,
    returns=_circle_result_type,
    select_result=_circle_result_spec,
    operation_id="zencad.typed.face.circle",
    operation_version="1",
)
def circle(
    r: float,
    angle: float | Sequence[float] | None = None,
    wire: bool = False,
) -> Face | Edge:
    _require_bool(wire, "circle wire")
    resolved = ops.circle_shape(r, _angle_values(angle, "circle angle"), wire)
    return Edge(resolved) if wire else Face(resolved)


def _ellipse_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Face | Edge]:
    return Edge if _wire_argument(args, kwargs, 3) else Face


def _ellipse_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    return EDGE_SPEC if _wire_argument(args, kwargs, 3) else FACE_SPEC


@overload
def ellipse(
    r1: float,
    r2: float,
    angle: float | Sequence[float] | None = None,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def ellipse(
    r1: float,
    r2: float,
    angle: float | Sequence[float] | None = None,
    *,
    wire: Literal[True],
) -> Edge: ...


@overload
def ellipse(
    r1: float,
    r2: float,
    angle: float | Sequence[float] | None,
    wire: Literal[True],
) -> Edge: ...


@overload
def ellipse(
    r1: float,
    r2: float,
    angle: float | Sequence[float] | None,
    wire: bool,
) -> Face | Edge: ...


@operation(
    result=FACE_SPEC,
    returns=_ellipse_result_type,
    select_result=_ellipse_result_spec,
    operation_id="zencad.typed.face.ellipse",
    operation_version="1",
)
def ellipse(
    r1: float,
    r2: float,
    angle: float | Sequence[float] | None = None,
    wire: bool = False,
) -> Face | Edge:
    _require_bool(wire, "ellipse wire")
    resolved = ops.ellipse_shape(r1, r2, _angle_values(angle, "ellipse angle"), wire)
    return Edge(resolved) if wire else Face(resolved)


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.fill",
    operation_version="1",
)
def fill(shapes: Edge | Wire | Sequence[Edge | Wire], /) -> Face:
    values = _require_wire_parts(shapes, "fill")
    return Face(ops.fill_wires(tuple(value._legacy() for value in values)))


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.interpolate2",
    operation_version="1",
)
def interpolate2(
    refs: Sequence[Sequence[Point3]],
    degmin: int = 3,
    degmax: int = 7,
) -> Face:
    if isinstance(refs, (str, bytes)) or not isinstance(refs, Sequence):
        raise TypeError("interpolate2 expects a point grid")
    rows = tuple(
        _require_points(row, minimum=2, name="interpolate2 row") for row in refs
    )
    if len(rows) < 2:
        raise ValueError("interpolate2 requires at least two rows")
    if len({len(row) for row in rows}) != 1:
        raise ValueError("interpolate2 point grid must be rectangular")
    degree_min = _require_positive_int(degmin, "interpolate2 degmin")
    degree_max = _require_positive_int(degmax, "interpolate2 degmax")
    if degree_min > degree_max:
        raise ValueError("interpolate2 degmin must not exceed degmax")
    return Face(
        ops.interpolate_face(
            tuple(tuple(point._resolved() for point in row) for row in rows),
            degree_min,
            degree_max,
        )
    )


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.fix",
    operation_version="1",
)
def fix_face(shape: Face, /) -> Face:
    if not isinstance(shape, Face):
        raise TypeError("fix_face expects Face")
    return Face(ops.fix_face(shape._legacy()))


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.infplane",
    operation_version="1",
)
def infplane() -> Face:
    return Face(ops.infinite_plane())


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.ruled",
    operation_version="1",
)
def ruled(first: Edge, second: Edge, /) -> Face:
    if not isinstance(first, Edge) or not isinstance(second, Edge):
        raise TypeError("ruled expects two Edge values")
    return Face(ops.ruled_face(first._legacy(), second._legacy()))


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.face.widewire",
    operation_version="1",
)
def widewire(
    spine: Edge | Wire,
    r: float,
    circled_joints: bool = True,
    circled_ends: bool = True,
) -> Shape:
    if not isinstance(spine, (Edge, Wire)):
        raise TypeError("widewire spine must be Edge or Wire")
    _require_bool(circled_joints, "widewire circled_joints")
    _require_bool(circled_ends, "widewire circled_ends")
    return Shape(ops.widewire(spine._legacy(), r, circled_joints, circled_ends))


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.fill",
    operation_version="1",
)
def _fill_shape(shape: Shape, /) -> Face:
    if not isinstance(shape, Shape):
        raise TypeError("Shape.fill expects Shape")
    return Face(ops.fill_shape(shape._legacy()))


def _require_positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


__all__ = [
    "circle",
    "ellipse",
    "fill",
    "fix_face",
    "infplane",
    "interpolate2",
    "ngon",
    "polygon",
    "rectangle",
    "rectangle_wire",
    "ruled",
    "square",
    "widewire",
]
