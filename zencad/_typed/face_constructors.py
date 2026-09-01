"""Typed planar face constructors declared at module level."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Literal, overload

from evalcache import ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.operation import (
    OperationArguments,
    arguments,
    operation,
    resolve_runtime,
    using_runtime,
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
    ScalarInput,
    _angle_state,
    _scalar_state,
    point3,
    scalar,
)


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


def _as_scalar(value: ScalarInput) -> Scalar:
    if isinstance(value, Scalar):
        return value
    return scalar(value)


@operation(
    backend=ops.polygon,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.polygon",
    operation_version="1",
)
def _polygon_face(points: Sequence[Point3], /) -> OperationArguments:
    return arguments(_require_points(points, minimum=3, name="polygon"))


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
    backend=ops.rectangle,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.rectangle",
    operation_version="1",
)
def _rectangle_face(
    width: ScalarInput,
    height: ScalarInput,
    center: bool,
    /,
) -> OperationArguments:
    _require_bool(center, "rectangle center")
    runtime = resolve_runtime(width, height)
    return arguments(
        _scalar_state(runtime, width),
        _scalar_state(runtime, height),
        center,
    )


def rectangle_wire(
    a: ScalarInput,
    b: ScalarInput,
    center: bool = False,
) -> Wire:
    _require_bool(center, "rectangle_wire center")
    runtime = resolve_runtime(a, b)
    with using_runtime(runtime):
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
    a: ScalarInput,
    b: ScalarInput | None = None,
    center: bool = False,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def rectangle(
    a: ScalarInput,
    b: ScalarInput | None = None,
    center: bool = False,
    *,
    wire: Literal[True],
) -> Wire: ...


@overload
def rectangle(
    a: ScalarInput,
    b: ScalarInput | None,
    center: bool,
    wire: Literal[True],
) -> Wire: ...


@overload
def rectangle(
    a: ScalarInput,
    b: ScalarInput | None,
    center: bool,
    wire: bool,
) -> Face | Wire: ...


def rectangle(
    a: ScalarInput,
    b: ScalarInput | None = None,
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
    a: ScalarInput,
    b: ScalarInput | None = None,
    center: bool = False,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def square(
    a: ScalarInput,
    b: ScalarInput | None = None,
    center: bool = False,
    *,
    wire: Literal[True],
) -> Wire: ...


@overload
def square(
    a: ScalarInput,
    b: ScalarInput | None,
    center: bool,
    wire: Literal[True],
) -> Wire: ...


@overload
def square(
    a: ScalarInput,
    b: ScalarInput | None,
    center: bool,
    wire: bool,
) -> Face | Wire: ...


def square(
    a: ScalarInput,
    b: ScalarInput | None = None,
    center: bool = False,
    wire: bool = False,
) -> Face | Wire:
    return rectangle(a, b, center, wire)


@overload
def ngon(r: ScalarInput, n: int, wire: Literal[False] = False) -> Face: ...


@overload
def ngon(r: ScalarInput, n: int, wire: Literal[True]) -> Wire: ...


@overload
def ngon(r: ScalarInput, n: int, wire: bool) -> Face | Wire: ...


def ngon(
    r: ScalarInput,
    n: int,
    wire: bool = False,
) -> Face | Wire:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("ngon n must be int")
    if n < 3:
        raise ValueError("ngon n must be at least 3")
    _require_bool(wire, "ngon wire")
    runtime = resolve_runtime(r)
    with using_runtime(runtime):
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
    r: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def circle(
    r: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    *,
    wire: Literal[True],
) -> Edge: ...


@overload
def circle(
    r: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None,
    wire: Literal[True],
) -> Edge: ...


@overload
def circle(
    r: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None,
    wire: bool,
) -> Face | Edge: ...


@operation(
    backend=ops.circle_shape,
    result=FACE_SPEC,
    returns=_circle_result_type,
    select_result=_circle_result_spec,
    operation_id="zencad.typed.face.circle",
    operation_version="1",
)
def circle(
    r: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    wire: bool = False,
) -> OperationArguments:
    _require_bool(wire, "circle wire")
    runtime = resolve_runtime(r, angle)
    return arguments(
        _scalar_state(runtime, r),
        _angle_state(runtime, angle, "circle angle"),
        wire,
    )


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
    r1: ScalarInput,
    r2: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    wire: Literal[False] = False,
) -> Face: ...


@overload
def ellipse(
    r1: ScalarInput,
    r2: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    *,
    wire: Literal[True],
) -> Edge: ...


@overload
def ellipse(
    r1: ScalarInput,
    r2: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None,
    wire: Literal[True],
) -> Edge: ...


@overload
def ellipse(
    r1: ScalarInput,
    r2: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None,
    wire: bool,
) -> Face | Edge: ...


@operation(
    backend=ops.ellipse_shape,
    result=FACE_SPEC,
    returns=_ellipse_result_type,
    select_result=_ellipse_result_spec,
    operation_id="zencad.typed.face.ellipse",
    operation_version="1",
)
def ellipse(
    r1: ScalarInput,
    r2: ScalarInput,
    angle: ScalarInput | Sequence[ScalarInput] | None = None,
    wire: bool = False,
) -> OperationArguments:
    _require_bool(wire, "ellipse wire")
    runtime = resolve_runtime(r1, r2, angle)
    return arguments(
        _scalar_state(runtime, r1),
        _scalar_state(runtime, r2),
        _angle_state(runtime, angle, "ellipse angle"),
        wire,
    )


@operation(
    backend=ops.fill_wires,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.fill",
    operation_version="1",
)
def fill(shapes: Edge | Wire | Sequence[Edge | Wire], /) -> OperationArguments:
    return arguments(_require_wire_parts(shapes, "fill"))


@operation(
    backend=ops.interpolate_face,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.interpolate2",
    operation_version="1",
)
def interpolate2(
    refs: Sequence[Sequence[Point3]],
    degmin: int = 3,
    degmax: int = 7,
) -> OperationArguments:
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
    return arguments(rows, degree_min, degree_max)


@operation(
    backend=ops.fix_face,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.fix",
    operation_version="1",
)
def fix_face(shape: Face, /) -> OperationArguments:
    if not isinstance(shape, Face):
        raise TypeError("fix_face expects Face")
    return arguments(shape)


@operation(
    backend=ops.infinite_plane,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.infplane",
    operation_version="1",
)
def infplane() -> OperationArguments:
    return arguments()


@operation(
    backend=ops.ruled_face,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.face.ruled",
    operation_version="1",
)
def ruled(first: Edge, second: Edge, /) -> OperationArguments:
    if not isinstance(first, Edge) or not isinstance(second, Edge):
        raise TypeError("ruled expects two Edge values")
    return arguments(first, second)


@operation(
    backend=ops.widewire,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.face.widewire",
    operation_version="1",
)
def widewire(
    spine: Edge | Wire,
    r: ScalarInput,
    circled_joints: bool = True,
    circled_ends: bool = True,
) -> OperationArguments:
    if not isinstance(spine, (Edge, Wire)):
        raise TypeError("widewire spine must be Edge or Wire")
    _require_bool(circled_joints, "widewire circled_joints")
    _require_bool(circled_ends, "widewire circled_ends")
    runtime = resolve_runtime(spine, r)
    return arguments(
        spine,
        _scalar_state(runtime, r),
        circled_joints,
        circled_ends,
    )


@operation(
    backend=ops.fill_shape,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.fill",
    operation_version="1",
)
def _fill_shape(shape: Shape, /) -> OperationArguments:
    if not isinstance(shape, Shape):
        raise TypeError("Shape.fill expects Shape")
    return arguments(shape)


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
