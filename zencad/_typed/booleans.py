"""Typed topology-zero and boolean operations declared at module level."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from zencad.operation import OperationArguments, arguments, operation, resolve_runtime

from . import _boolean_operations as ops
from .topology import SHAPE_SPEC, Shape
from .values import Point3, ScalarInput, Vector3

if TYPE_CHECKING:
    from .runtime import Runtime


@operation(
    backend=ops.empty_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.empty_shape",
    operation_version="1",
)
def empty_shape() -> OperationArguments:
    """Return the algebraic zero of topology without materializing it."""

    return arguments()


def nullshape() -> Shape:
    """Legacy spelling for :func:`empty_shape`."""

    return empty_shape()


@operation(
    backend=ops.union_shapes,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.union",
    operation_version="1",
)
def union(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> OperationArguments:
    return arguments(_require_shapes(shapes, others, "union"))


@operation(
    backend=ops.intersection_shapes,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.intersect",
    operation_version="1",
)
def intersect(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> OperationArguments:
    return arguments(_require_shapes(shapes, others, "intersect"))


def intersection(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> Shape:
    """Descriptive alias for the legacy :func:`intersect` spelling."""

    return intersect(shapes, *others)


@operation(
    backend=ops.difference_shapes,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.difference",
    operation_version="1",
)
def difference(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> OperationArguments:
    return arguments(_require_shapes(shapes, others, "difference"))


@operation(
    backend=ops.section,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.section",
    operation_version="1",
)
def section(
    left: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput],
    right: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput] = 0,
    /,
    *,
    pretty: bool = False,
) -> OperationArguments:
    """Intersect shape boundaries, accepting legacy plane operands."""

    _require_bool(pretty, "section pretty")
    runtime = resolve_runtime(left, right)
    return arguments(
        _section_operand(runtime, left, "section left"),
        _section_operand(runtime, right, "section right"),
        pretty,
    )


@operation(
    backend=ops.union,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.union",
    operation_version="1",
)
def _shape_union(left: Shape, right: Shape) -> OperationArguments:
    _require_binary_shapes(left, right, "union")
    return arguments(left, right)


@operation(
    backend=ops.difference,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.difference",
    operation_version="1",
)
def _shape_difference(left: Shape, right: Shape) -> OperationArguments:
    _require_binary_shapes(left, right, "difference")
    return arguments(left, right)


@operation(
    backend=ops.intersection,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.intersection",
    operation_version="1",
)
def _shape_intersection(left: Shape, right: Shape) -> OperationArguments:
    _require_binary_shapes(left, right, "intersection")
    return arguments(left, right)


def _require_binary_shapes(left: Shape, right: Shape, name: str) -> None:
    if not isinstance(left, Shape) or not isinstance(right, Shape):
        raise TypeError(f"Shape {name} expects Shape")


def _require_shapes(
    shapes: Shape | Sequence[Shape],
    others: tuple[Shape, ...],
    name: str,
) -> tuple[Shape, ...]:
    if isinstance(shapes, Shape):
        values = (shapes, *others)
    elif isinstance(shapes, Sequence) and not isinstance(shapes, (str, bytes)):
        if others:
            raise TypeError(
                f"{name} cannot combine a Shape sequence with extra operands"
            )
        values = tuple(shapes)
    else:
        raise TypeError(f"{name} expects Shape operands or a sequence of Shape")
    if not values:
        raise ValueError(f"{name} requires at least one Shape")
    if not all(isinstance(shape, Shape) for shape in values):
        raise TypeError(f"{name} expects only Shape operands")
    return values


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _section_operand(
    runtime: Runtime,
    value: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput],
    name: str,
) -> Shape:
    if isinstance(value, Shape):
        return value
    if isinstance(value, (Point3, Vector3)):
        direction = runtime.vector3(value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        coordinates = tuple(value)
        if len(coordinates) != 3:
            raise TypeError(f"{name} plane vector must contain three coordinates")
        direction = runtime.vector3(coordinates)
    else:
        return runtime.halfspace().up(cast(ScalarInput, value))
    transform = runtime.translation(direction) * runtime.short_rotate(
        runtime.vector3(0, 0, 1), direction
    )
    return runtime.halfspace().transform(transform)


__all__ = [
    "difference",
    "empty_shape",
    "intersect",
    "intersection",
    "nullshape",
    "section",
    "union",
]
