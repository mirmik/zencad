"""Typed collections of similarity transforms."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, TypeVar

from ._core import require_same_context
from .topology import Shape
from .transforms import Transform

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
