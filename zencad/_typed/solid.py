"""Typed solid primitives declared as module-level domain operations."""

from __future__ import annotations

from collections.abc import Sequence

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.BRepLib import BRepLib_MakeFace
from OCP.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeHalfSpace,
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeTorus,
)
from OCP.gp import gp_Ax2, gp_Dir, gp_Pln, gp_Pnt
from OCP.ShapeFix import ShapeFix_Solid

from zencad.operation import operation

from .topology import SOLID_SPEC, Shell, Solid
from .values import Vector3


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.box",
    operation_version="1",
)
def box(
    x: float | Vector3 | Sequence[float] = 0,
    y: float | None = None,
    z: float | None = None,
    center: bool | str | None = None,
    size: float | Vector3 | Sequence[float] | None = None,
) -> Solid:
    """Build a box from concrete dimensions."""

    resolved_center = _require_center(center, "box center")
    length, width, height = _box_dimensions(x, y, z, size)
    origin = gp_Pnt(0, 0, 0)
    if resolved_center is True:
        origin = gp_Pnt(-length / 2, -width / 2, -height / 2)
    elif isinstance(resolved_center, str):
        origin = gp_Pnt(
            -length / 2 if "x" in resolved_center else 0,
            -width / 2 if "y" in resolved_center else 0,
            -height / 2 if "z" in resolved_center else 0,
        )
    builder = (
        BRepPrimAPI_MakeBox(
            gp_Ax2(origin, gp_Dir(0, 0, 1)),
            length,
            width,
            height,
        )
        if resolved_center
        else BRepPrimAPI_MakeBox(length, width, height)
    )
    return Solid(builder.Shape())


def cube(
    x: float | Vector3 | Sequence[float] = 0,
    y: float | None = None,
    z: float | None = None,
    center: bool | str | None = None,
    size: float | Vector3 | Sequence[float] | None = None,
) -> Solid:
    """Compatibility alias for :func:`box` with the legacy signature."""

    return box(x, y, z, center, size)


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.sphere",
    operation_version="1",
)
def sphere(
    r: float,
    yaw: float | None = None,
    pitch: float | tuple[float, float] | None = None,
) -> Solid:
    if yaw is None and pitch is None:
        native = BRepPrimAPI_MakeSphere(r).Shape()
    elif yaw is None:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeSphere(r, start, finish).Shape()
    elif pitch is None:
        native = BRepPrimAPI_MakeSphere(r, yaw).Shape()
    else:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeSphere(r, start, finish, yaw).Shape()
    return Solid(native)


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.cylinder",
    operation_version="1",
)
def cylinder(
    r: float,
    h: float,
    yaw: float | None = None,
    center: bool = False,
) -> Solid:
    _require_bool(center, "cylinder center")
    axis = gp_Ax2(
        gp_Pnt(0, 0, -h / 2 if center else 0),
        gp_Dir(0, 0, 1),
    )
    builder = (
        BRepPrimAPI_MakeCylinder(axis, r, h, yaw)
        if yaw is not None
        else BRepPrimAPI_MakeCylinder(axis, r, h)
    )
    return Solid(builder.Shape())


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.cone",
    operation_version="1",
)
def cone(
    r1: float,
    r2: float,
    h: float,
    yaw: float | None = None,
    center: bool = False,
) -> Solid:
    _require_bool(center, "cone center")
    axis = gp_Ax2(
        gp_Pnt(0, 0, -h / 2 if center else 0),
        gp_Dir(0, 0, 1),
    )
    builder = (
        BRepPrimAPI_MakeCone(axis, r1, r2, h, yaw)
        if yaw is not None
        else BRepPrimAPI_MakeCone(axis, r1, r2, h)
    )
    return Solid(builder.Shape())


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.torus",
    operation_version="1",
)
def torus(
    r1: float,
    r2: float,
    yaw: float | None = None,
    pitch: float | tuple[float, float] | None = None,
) -> Solid:
    if yaw is None and pitch is None:
        native = BRepPrimAPI_MakeTorus(r1, r2).Shape()
    elif yaw is None:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeTorus(r1, r2, start, finish).Shape()
    elif pitch is None:
        native = BRepPrimAPI_MakeTorus(r1, r2, yaw).Shape()
    else:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeTorus(r1, r2, start, finish, yaw).Shape()
    return Solid(native)


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.halfspace",
    operation_version="1",
)
def halfspace() -> Solid:
    face = BRepLib_MakeFace(gp_Pln()).Face()
    return Solid(BRepPrimAPI_MakeHalfSpace(face, gp_Pnt(0, 0, -1)).Solid())


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.make_solid",
    operation_version="1",
)
def make_solid(shells: Shell | Sequence[Shell], /) -> Solid:
    values = _require_shells(shells, "make_solid")
    builder = BRepBuilderAPI_MakeSolid()
    for shell in values:
        builder.Add(shell._legacy().Shell())
    fixer = ShapeFix_Solid(builder.Solid())
    fixer.Perform()
    return Solid(fixer.Solid())


def _require_center(
    value: bool | str | None,
    name: str,
) -> bool | str | None:
    if value is not None and not isinstance(value, (bool, str)):
        raise TypeError(f"{name} must be bool, str, or None")
    return value


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_shells(
    shells: Shell | Sequence[Shell],
    name: str,
) -> tuple[Shell, ...]:
    values: tuple[Shell, ...]
    if isinstance(shells, Shell):
        values = (shells,)
    elif isinstance(shells, Sequence) and not isinstance(shells, (str, bytes)):
        values = tuple(shells)
    else:
        raise TypeError(f"{name} expects Shell or a sequence of Shell")
    if not values:
        raise ValueError(f"{name} requires at least one Shell")
    if not all(isinstance(shell, Shell) for shell in values):
        raise TypeError(f"{name} expects only Shell values")
    return values


def _box_dimensions(
    x: float | Vector3 | Sequence[float],
    y: float | None,
    z: float | None,
    size: float | Vector3 | Sequence[float] | None,
) -> tuple[float, float, float]:
    source = x if size is None else size
    if size is not None:
        y = None
        z = None
    if isinstance(source, Vector3):
        if y is not None or z is not None:
            raise TypeError("box Vector3 size cannot be combined with y or z")
        return source.value()
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
        if y is not None or z is not None:
            raise TypeError("box sequence size cannot be combined with y or z")
        values = tuple(source)
        if len(values) != 3:
            raise TypeError("box size must contain exactly three dimensions")
        return (float(values[0]), float(values[1]), float(values[2]))
    scalar = float(source)
    if y is None and z is None:
        return (scalar, scalar, scalar)
    if y is not None and z is not None:
        return (scalar, float(y), float(z))
    raise TypeError("box expects one size or all three dimensions")


def _angle_pair(value: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, tuple):
        if len(value) != 2:
            raise TypeError("angle interval expects exactly two scalar bounds")
        return value
    return (-value / 2, value / 2)


__all__ = [
    "box",
    "cone",
    "cube",
    "cylinder",
    "halfspace",
    "make_solid",
    "sphere",
    "torus",
]
