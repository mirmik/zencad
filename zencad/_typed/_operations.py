"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

from dataclasses import dataclass

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import _box
from zencad.geom.trans import move


@dataclass(frozen=True)
class PointValue:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class VectorValue:
    x: float
    y: float
    z: float


def box(x: float, y: float | None, z: float | None, center: bool) -> ResolvedShape:
    return _box(x, y, z, center=center)


def translate(shape: ResolvedShape, vector: VectorValue) -> ResolvedShape:
    return shape.transform(move(vector.x, vector.y, vector.z))


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left - right


def faces(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return tuple(shape.faces())


def sequence_item(sequence: tuple[ResolvedShape, ...], index: int) -> ResolvedShape:
    return sequence[index]


def mass(shape: ResolvedShape) -> float:
    return float(shape.mass())


def center(shape: ResolvedShape) -> PointValue:
    value = shape.center()
    return PointValue(float(value.x), float(value.y), float(value.z))


def point(x: float, y: float, z: float) -> PointValue:
    return PointValue(x, y, z)


def vector(x: float, y: float, z: float) -> VectorValue:
    return VectorValue(x, y, z)


def point_coordinate(value: PointValue, axis: int) -> float:
    return (value.x, value.y, value.z)[axis]


def vector_coordinate(value: VectorValue, axis: int) -> float:
    return (value.x, value.y, value.z)[axis]


def scalar_add(left: float, right: float) -> float:
    return left + right


def scalar_subtract(left: float, right: float) -> float:
    return left - right


def scalar_multiply(left: float, right: float) -> float:
    return left * right


def scalar_divide(left: float, right: float) -> float:
    return left / right
