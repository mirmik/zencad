"""Resolved solid primitive operations for the typed domain layer."""

from __future__ import annotations

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import (
    _box,
    _cone,
    _cylinder,
    _halfspace,
    _make_solid,
    _sphere,
    _torus,
)

from ._value_operations import Vector3Value


def box(
    size: Vector3Value,
    center: bool | str | None,
) -> ResolvedShape:
    return _box(size.x, size.y, size.z, center=center)


def sphere(
    radius: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    return _sphere(radius, yaw=yaw, pitch=pitch)


def cylinder(
    radius: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    return _cylinder(radius, height, yaw=yaw, center=center)


def cone(
    radius1: float,
    radius2: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    return _cone(radius1, radius2, height, yaw=yaw, center=center)


def torus(
    radius1: float,
    radius2: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    return _torus(radius1, radius2, yaw=yaw, pitch=pitch)


def halfspace() -> ResolvedShape:
    return _halfspace()


def make_solid(shells: tuple[ResolvedShape, ...]) -> ResolvedShape:
    return _make_solid(shells)
