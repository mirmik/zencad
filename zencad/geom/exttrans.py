"""Typed collections of similarity transforms."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
import math
from typing import TYPE_CHECKING, TypeVar

from zencad.operation import resolve_context, using_context

from ._core import require_same_context
from .records import Interval
from .topology import Shape
from .transforms import Transform, right, rotateX, rotateZ
from .values import ScalarInput

if TYPE_CHECKING:
    from .context import Context


ShapeT = TypeVar("ShapeT", bound=Shape)


class MultiTransform:
    """An immutable transform sequence whose members retain their lazy graphs."""

    __slots__ = ("_context", "_transforms", "array", "unit")

    def __init__(
        self,
        transforms: Sequence[Transform],
        *,
        context: Context,
        array: bool = False,
        unit: bool = False,
    ) -> None:
        if not isinstance(array, bool) or not isinstance(unit, bool):
            raise TypeError("MultiTransform array and unit flags must be bool")
        resolved = tuple(transforms)
        for transform in resolved:
            if not isinstance(transform, Transform):
                raise TypeError("MultiTransform expects Transform items")
            require_same_context(context, transform)
        self._context = context
        self._transforms = resolved
        self.array = array
        self.unit = unit

    @property
    def context(self) -> Context:
        return self._context

    @property
    def transforms(self) -> tuple[Transform, ...]:
        return self._transforms

    def __len__(self) -> int:
        return len(self._transforms)

    def __iter__(self) -> Iterator[Transform]:
        return iter(self._transforms)

    def items(self, shape: ShapeT, /) -> list[ShapeT]:
        if not isinstance(shape, Shape):
            raise TypeError("MultiTransform.items expects Shape")
        require_same_context(self.context, shape)
        return [shape.transform(transform) for transform in self._transforms]

    def fused(self, shape: Shape, /) -> Shape:
        items = self.items(shape)
        if not items:
            raise ValueError("cannot fuse an empty MultiTransform")
        result: Shape = items[0]
        for item in items[1:]:
            result = result + item
        return result

    def __call__(self, shape: ShapeT, /) -> Shape | list[ShapeT]:
        if self.array:
            return self.items(shape)
        return self.fused(shape)


def _count(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("rotate array count must be int")
    if value < 1:
        raise ValueError("rotate array count must be positive")
    return value


def _interval(value: Interval | Sequence[ScalarInput], name: str):
    if isinstance(value, Interval):
        return (value.lower, value.upper)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must contain two angles")
    values = tuple(value)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two angles")
    return values


def _linspace(start: ScalarInput, stop: ScalarInput, count: int, endpoint: bool):
    if count == 1:
        return (start,)
    divisor = count - 1 if endpoint else count
    step = (stop - start) / divisor
    return tuple(start + step * index for index in range(count))


def rotate_array(
    n: int,
    yaw: ScalarInput = 2 * math.pi,
    endpoint: bool = False,
    array: bool = False,
    unit: bool = False,
) -> MultiTransform:
    """Create evenly spaced rotations around the Z axis."""

    count = _count(n)
    if not isinstance(endpoint, bool):
        raise TypeError("rotate_array endpoint must be bool")
    context = resolve_context(yaw)
    with using_context(context):
        angles = _linspace(0, yaw, count, endpoint)
        transforms = tuple(rotateZ(angle) for angle in angles)
    return MultiTransform(transforms, context=context, array=array, unit=unit)


def rotate_array2(
    n: int,
    r: ScalarInput | None = None,
    yaw: Interval | Sequence[ScalarInput] = (0, 2 * math.pi),
    roll: Interval | Sequence[ScalarInput] = (0, 0),
    endpoint: bool = False,
    array: bool = False,
    unit: bool = False,
) -> MultiTransform:
    """Create radial transforms with independently interpolated yaw and roll."""

    count = _count(n)
    if not isinstance(endpoint, bool):
        raise TypeError("rotate_array2 endpoint must be bool")
    yaw_start, yaw_stop = _interval(yaw, "rotate_array2 yaw")
    roll_start, roll_stop = _interval(roll, "rotate_array2 roll")
    radius = 0 if r is None else r
    context = resolve_context(radius, yaw_start, yaw_stop, roll_start, roll_stop)
    with using_context(context):
        yaws = _linspace(yaw_start, yaw_stop, count, endpoint)
        rolls = _linspace(roll_start, roll_stop, count, endpoint)
        transforms = tuple(
            rotateZ(yaw_angle)
            * right(radius)
            * rotateX(math.pi / 2)
            * rotateZ(roll_angle)
            for yaw_angle, roll_angle in zip(yaws, rolls)
        )
    return MultiTransform(transforms, context=context, array=array, unit=unit)
