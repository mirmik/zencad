"""Typed topology-zero and boolean operations declared at module level."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from evalcache import Expression

from zencad.operation import (
    OperationArguments,
    arguments,
    operation,
    resolve_runtime,
    using_runtime,
)

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
from .values import Point3, ScalarInput, Vector3, vector3

if TYPE_CHECKING:
    from zencad.geom.shape import Shape as ResolvedShape

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


class SplitResult(DeferredSequence[Solid]):
    """Deferred, deterministic sequence of split solids."""

    @classmethod
    def _from_state(
        cls,
        runtime: Runtime,
        state: State[tuple[ResolvedShape, ...]],
    ) -> SplitResult:
        if not isinstance(state, Expression):
            raise TypeError("typed split results require an expression state")
        return cls(
            runtime,
            state,
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
    backend=ops.split_shapes,
    result=_SOLID_SEQUENCE_SPEC,
    returns=SplitResult,
    operation_id="zencad.typed.split",
    operation_version="1",
)
def split(
    body: Shape,
    tools: Shape | Sequence[Shape],
    /,
) -> OperationArguments:
    if not isinstance(body, Shape):
        raise TypeError("split body must be a Shape")
    return arguments(body, _require_shapes(tools, (), "split"))


@operation(
    backend=ops.slice_shape,
    result=_SOLID_SEQUENCE_SPEC,
    returns=SliceResult,
    operation_id="zencad.typed.slice",
    operation_version="1",
)
def slice(
    body: Shape,
    z: ScalarInput = 0,
    *,
    axis: object = "z",
    plane: object | None = None,
) -> OperationArguments:
    if not isinstance(body, Shape):
        raise TypeError("slice body must be a Shape")
    if plane is not None and not (
        isinstance(z, (int, float)) and not isinstance(z, bool) and z == 0
    ):
        raise TypeError("slice accepts either z/axis or plane, not both")
    return arguments(body, plane, z, axis)


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
    with using_runtime(runtime):
        if isinstance(value, (Point3, Vector3)):
            direction = vector3(value)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            coordinates = tuple(value)
            if len(coordinates) != 3:
                raise TypeError(f"{name} plane vector must contain three coordinates")
            direction = vector3(coordinates)
        else:
            return halfspace().transform(moveZ(cast(ScalarInput, value)))
        transform = translation(direction) * short_rotate(
            vector3(0, 0, 1), direction
        )
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
