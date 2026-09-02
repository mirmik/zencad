"""Small typed structured records composed from graph-preserving handles."""

from __future__ import annotations

from collections.abc import Iterator
from typing import overload

from ._core import require_same_context
from .values import Point3, Scalar, Vector3


class Interval:
    """A named pair of Scalar bounds that keeps both expression states."""

    __slots__ = ("_lower", "_upper")
    __hash__ = None

    def __init__(self, lower: Scalar, upper: Scalar, /) -> None:
        if not isinstance(lower, Scalar) or not isinstance(upper, Scalar):
            raise TypeError("Interval bounds must be Scalar")
        require_same_context(lower.context, upper)
        self._lower = lower
        self._upper = upper

    @property
    def lower(self) -> Scalar:
        return self._lower

    @property
    def upper(self) -> Scalar:
        return self._upper

    def length(self) -> Scalar:
        return self._upper - self._lower

    def value(self) -> tuple[float, float]:
        """Materialize both bounds as a fixed Python tuple."""
        return (self._lower.value(), self._upper.value())

    def __zencad_arguments__(self) -> tuple[Scalar, Scalar]:
        """Expose graph operands when an interval crosses an operation boundary."""
        return (self._lower, self._upper)

    def __iter__(self) -> Iterator[Scalar]:
        return iter((self._lower, self._upper))

    def __len__(self) -> int:
        return 2

    @overload
    def __getitem__(self, index: int, /) -> Scalar: ...

    @overload
    def __getitem__(self, index: slice, /) -> tuple[Scalar, ...]: ...

    def __getitem__(self, index: int | slice, /) -> Scalar | tuple[Scalar, ...]:
        return (self._lower, self._upper)[index]


class LineParameters:
    __slots__ = ("origin", "direction")

    def __init__(self, origin: Point3, direction: Vector3, /) -> None:
        require_same_context(origin.context, direction)
        self.origin = origin
        self.direction = direction

    def __iter__(self) -> Iterator[Point3 | Vector3]:
        return iter((self.origin, self.direction))


class CircleParameters:
    __slots__ = ("center", "radius", "x_direction", "y_direction")

    def __init__(
        self,
        center: Point3,
        radius: Scalar,
        x_direction: Vector3,
        y_direction: Vector3,
        /,
    ) -> None:
        for value in (radius, x_direction, y_direction):
            require_same_context(center.context, value)
        self.center = center
        self.radius = radius
        self.x_direction = x_direction
        self.y_direction = y_direction

    def __iter__(self) -> Iterator[Point3 | Scalar | Vector3]:
        return iter((self.center, self.radius, self.x_direction, self.y_direction))


class EllipseParameters:
    __slots__ = (
        "center",
        "major_radius",
        "minor_radius",
        "x_direction",
        "y_direction",
    )

    def __init__(
        self,
        center: Point3,
        major_radius: Scalar,
        minor_radius: Scalar,
        x_direction: Vector3,
        y_direction: Vector3,
        /,
    ) -> None:
        for value in (major_radius, minor_radius, x_direction, y_direction):
            require_same_context(center.context, value)
        self.center = center
        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.x_direction = x_direction
        self.y_direction = y_direction

    def __iter__(self) -> Iterator[Point3 | Scalar | Vector3]:
        return iter(
            (
                self.center,
                self.major_radius,
                self.minor_radius,
                self.x_direction,
                self.y_direction,
            )
        )


class ShapeProperties:
    """Named graph-preserving mass and center result."""

    __slots__ = ("center", "mass")

    def __init__(self, center: Point3, mass: Scalar, /) -> None:
        require_same_context(center.context, mass)
        self.center = center
        self.mass = mass

    def __iter__(self) -> Iterator[Point3 | Scalar]:
        return iter((self.center, self.mass))


class CurveProjection:
    """Nearest curve projection expressed entirely as typed graph handles."""

    __slots__ = ("point", "parameter", "distance")

    def __init__(
        self,
        point: Point3,
        parameter: Scalar,
        distance: Scalar,
        /,
    ) -> None:
        require_same_context(point.context, parameter)
        require_same_context(point.context, distance)
        self.point = point
        self.parameter = parameter
        self.distance = distance

    def value(self) -> tuple[tuple[float, float, float], float, float]:
        return (self.point.value(), self.parameter.value(), self.distance.value())
