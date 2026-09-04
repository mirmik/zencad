"""Resolved operations for immutable typed boundary boxes."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from OCP.Bnd import Bnd_Box

from zencad._native.shape import Shape as ResolvedShape
from zencad.occ_compat import add_to_bounds

from ._value_operations import Point3Value, Vector3Value


@dataclass(frozen=True, slots=True)
class BoundaryBoxValue:
    """Six axis bounds, or ``None`` for an empty box."""

    coordinates: tuple[float, float, float, float, float, float] | None

    def __post_init__(self) -> None:
        if self.coordinates is None:
            return
        if len(self.coordinates) != 6:
            raise ValueError("BoundaryBoxValue requires six coordinates")
        if not all(type(value) is float for value in self.coordinates):
            raise TypeError("BoundaryBoxValue coordinates must be floats")
        if any(math.isnan(value) for value in self.coordinates):
            raise ValueError("BoundaryBoxValue coordinates cannot be NaN")
        xmin, xmax, ymin, ymax, zmin, zmax = self.coordinates
        if xmin > xmax or ymin > ymax or zmin > zmax:
            raise ValueError("BoundaryBoxValue minimum exceeds maximum")

    @property
    def is_empty(self) -> bool:
        return self.coordinates is None

    def __evalcache_key__(self) -> bytes:
        if self.coordinates is None:
            return b"zencad-boundary-box-value-v1\x00empty"
        return b"zencad-boundary-box-value-v1\x00bounds" + struct.pack(
            ">6d", *self.coordinates
        )


def empty_boundary_box() -> BoundaryBoxValue:
    return BoundaryBoxValue(None)


def boundary_box_from_points(
    minimum: Point3Value,
    maximum: Point3Value,
) -> BoundaryBoxValue:
    return BoundaryBoxValue(
        (
            float(minimum.x),
            float(maximum.x),
            float(minimum.y),
            float(maximum.y),
            float(minimum.z),
            float(maximum.z),
        )
    )


def boundary_box_from_ocp(value: Bnd_Box) -> BoundaryBoxValue:
    if not isinstance(value, Bnd_Box):
        raise TypeError("boundary_box_from_ocp expects Bnd_Box")
    if value.IsVoid():
        return empty_boundary_box()
    xmin, ymin, zmin, xmax, ymax, zmax = value.Get()
    return BoundaryBoxValue(
        (
            float(xmin),
            float(xmax),
            float(ymin),
            float(ymax),
            float(zmin),
            float(zmax),
        )
    )


def boundary_box_to_ocp(value: BoundaryBoxValue) -> Bnd_Box:
    if not isinstance(value, BoundaryBoxValue):
        raise TypeError("boundary_box_to_ocp expects BoundaryBoxValue")
    box = Bnd_Box()
    if value.coordinates is not None:
        xmin, xmax, ymin, ymax, zmin, zmax = value.coordinates
        box.Update(xmin, ymin, zmin, xmax, ymax, zmax)
    return box


def valid_boundary_box(value: BoundaryBoxValue) -> bool:
    try:
        boundary_box_to_ocp(value)
    except (TypeError, ValueError, RuntimeError):
        return False
    return True


def shape_boundary_box(shape: ResolvedShape) -> BoundaryBoxValue:
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("cannot compute bounds of a null shape")
    box = Bnd_Box()
    add_to_bounds(native, box)
    return boundary_box_from_ocp(box)


def boundary_box_union(
    left: BoundaryBoxValue,
    right: BoundaryBoxValue,
) -> BoundaryBoxValue:
    if left.coordinates is None:
        return right
    if right.coordinates is None:
        return left
    lx0, lx1, ly0, ly1, lz0, lz1 = left.coordinates
    rx0, rx1, ry0, ry1, rz0, rz1 = right.coordinates
    return BoundaryBoxValue(
        (
            min(lx0, rx0),
            max(lx1, rx1),
            min(ly0, ry0),
            max(ly1, ry1),
            min(lz0, rz0),
            max(lz1, rz1),
        )
    )


def boundary_box_coordinate(value: BoundaryBoxValue, index: int) -> float:
    if value.coordinates is None:
        raise ValueError("empty BoundaryBox has no coordinates")
    return value.coordinates[index]


def boundary_box_point(value: BoundaryBoxValue, upper: bool) -> Point3Value:
    if value.coordinates is None:
        raise ValueError("empty BoundaryBox has no corner points")
    xmin, xmax, ymin, ymax, zmin, zmax = value.coordinates
    if upper:
        return Point3Value(xmax, ymax, zmax)
    return Point3Value(xmin, ymin, zmin)


def boundary_box_size(value: BoundaryBoxValue) -> Vector3Value:
    if value.coordinates is None:
        raise ValueError("empty BoundaryBox has no size")
    xmin, xmax, ymin, ymax, zmin, zmax = value.coordinates
    return Vector3Value(xmax - xmin, ymax - ymin, zmax - zmin)


def boundary_box_center(value: BoundaryBoxValue) -> Point3Value:
    if value.coordinates is None:
        raise ValueError("empty BoundaryBox has no center")
    xmin, xmax, ymin, ymax, zmin, zmax = value.coordinates
    return Point3Value(
        (xmin + xmax) / 2,
        (ymin + ymax) / 2,
        (zmin + zmax) / 2,
    )
