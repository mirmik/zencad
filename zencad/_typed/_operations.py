"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import _box
from zencad.geom.trans import move

from ._value_operations import Point3Value, Vector3Value


def box(x: float, y: float | None, z: float | None, center: bool) -> ResolvedShape:
    return _box(x, y, z, center=center)


def translate(shape: ResolvedShape, vector: Vector3Value) -> ResolvedShape:
    return shape.transform(move(vector.x, vector.y, vector.z))


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left - right


def faces(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return tuple(shape.faces())


def sequence_item(sequence: tuple[ResolvedShape, ...], index: int) -> ResolvedShape:
    return sequence[index]


def mass(shape: ResolvedShape) -> float:
    return float(shape.mass())


def center(shape: ResolvedShape) -> Point3Value:
    value = shape.center()
    return Point3Value(float(value.x), float(value.y), float(value.z))
