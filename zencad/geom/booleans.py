"""Typed topology-zero and boolean operations declared at module level."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from zencad.operation import execution_context, operation, using_context

from . import _boolean_operations as ops
from .solid import halfspace
from ._core import State
from .topology import (
    SHAPE_SPEC,
    SOLID_SPEC,
    DeferredSequence,
    Shape,
    Solid,
    _SOLID_SEQUENCE_SPEC,
)
from .transforms import moveZ, short_rotate, translation
from .values import Point3, Vector3, vector3

if TYPE_CHECKING:
    from zencad._native.shape import Shape as ResolvedShape

    from .context import Context


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.empty_shape",
    operation_version="1",
)
def empty_shape() -> Shape:
    """Return the algebraic zero of topology without materializing it."""

    return Shape(ops.empty_shape())


def nullshape() -> Shape:
    """Legacy spelling for :func:`empty_shape`."""

    return empty_shape()


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.union",
    operation_version="2",
)
def union(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> Shape:
    values = _require_shapes(shapes, others, "union")
    return Shape(ops.union_shapes(tuple(shape._legacy() for shape in values)))


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.intersect",
    operation_version="1",
)
def intersect(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> Shape:
    values = _require_shapes(shapes, others, "intersect")
    return Shape(ops.intersection_shapes(tuple(shape._legacy() for shape in values)))


def intersection(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> Shape:
    """Descriptive alias for the legacy :func:`intersect` spelling."""

    return intersect(shapes, *others)


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.difference",
    operation_version="1",
)
def difference(
    shapes: Shape | Sequence[Shape],
    /,
    *others: Shape,
) -> Shape:
    values = _require_shapes(shapes, others, "difference")
    return Shape(ops.difference_shapes(tuple(shape._legacy() for shape in values)))


class SplitResult(DeferredSequence[Solid]):
    """Deferred, deterministic sequence of split solids."""

    @classmethod
    def _from_state(
        cls,
        context: Context,
        state: State[tuple[ResolvedShape, ...]],
    ) -> SplitResult:
        return cls(
            context,
            state,
            sequence_spec=_SOLID_SEQUENCE_SPEC,
            item_type=Solid,
            item_spec=SOLID_SPEC,
            operation_id="zencad.typed.split.item",
        )


class SliceResult(SplitResult):
    """Two split solids ordered from negative to positive plane side."""

    @property
    def lower(self) -> Solid:
        return self[0]

    @property
    def upper(self) -> Solid:
        return self[1]


@operation(
    result=_SOLID_SEQUENCE_SPEC,
    returns=SplitResult,
    operation_id="zencad.typed.split",
    operation_version="1",
)
def split(
    body: Shape,
    tools: Shape | Sequence[Shape],
    /,
) -> SplitResult:
    if not isinstance(body, Shape):
        raise TypeError("split body must be a Shape")
    values = _require_shapes(tools, (), "split")
    return SplitResult._from_state(
        execution_context(),
        ops.split_shapes(body._legacy(), tuple(tool._legacy() for tool in values)),
    )


@operation(
    result=_SOLID_SEQUENCE_SPEC,
    returns=SliceResult,
    operation_id="zencad.typed.slice",
    operation_version="1",
)
def slice(
    body: Shape,
    z: float = 0,
    *,
    axis: object = "z",
    plane: object | None = None,
) -> SliceResult:
    if not isinstance(body, Shape):
        raise TypeError("slice body must be a Shape")
    if plane is not None and not (
        isinstance(z, (int, float)) and not isinstance(z, bool) and z == 0
    ):
        raise TypeError("slice accepts either z/axis or plane, not both")
    resolved_plane = plane._legacy() if isinstance(plane, Shape) else plane
    return SliceResult._from_state(
        execution_context(),
        ops.slice_shape(body._legacy(), resolved_plane, z, axis),
    )


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.section",
    operation_version="1",
)
def section(
    left: Shape | float | Point3 | Vector3 | Sequence[float],
    right: Shape | float | Point3 | Vector3 | Sequence[float] = 0,
    /,
    *,
    pretty: bool = False,
) -> Shape:
    """Intersect shape boundaries, accepting legacy plane operands."""

    _require_bool(pretty, "section pretty")
    context = execution_context()
    left_shape = _section_operand(context, left, "section left")
    right_shape = _section_operand(context, right, "section right")
    return Shape(ops.section(left_shape._legacy(), right_shape._legacy(), pretty))


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.union",
    operation_version="2",
)
def _shape_union(left: Shape, right: Shape) -> Shape:
    _require_binary_shapes(left, right, "union")
    return Shape(ops.union(left._legacy(), right._legacy()))


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.difference",
    operation_version="1",
)
def _shape_difference(left: Shape, right: Shape) -> Shape:
    _require_binary_shapes(left, right, "difference")
    return Shape(ops.difference(left._legacy(), right._legacy()))


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.intersection",
    operation_version="1",
)
def _shape_intersection(left: Shape, right: Shape) -> Shape:
    _require_binary_shapes(left, right, "intersection")
    return Shape(ops.intersection(left._legacy(), right._legacy()))


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
    context: Context,
    value: Shape | float | Point3 | Vector3 | Sequence[float],
    name: str,
) -> Shape:
    if isinstance(value, Shape):
        return value
    with using_context(context):
        if isinstance(value, (Point3, Vector3)):
            direction = vector3(value)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            coordinates = tuple(value)
            if len(coordinates) != 3:
                raise TypeError(f"{name} plane vector must contain three coordinates")
            direction = vector3(coordinates)
        else:
            return halfspace().transform(moveZ(cast(float, value)))
        transform = translation(direction) * short_rotate(vector3(0, 0, 1), direction)
        return halfspace().transform(transform)


__all__ = [
    "SliceResult",
    "SplitResult",
    "difference",
    "empty_shape",
    "intersect",
    "intersection",
    "nullshape",
    "section",
    "slice",
    "split",
    "union",
]
