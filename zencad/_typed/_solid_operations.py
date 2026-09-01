"""Resolved solid primitive operations for the typed domain layer."""

from __future__ import annotations

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
from OCP.ShapeFix import ShapeFix_Solid
from OCP.gp import gp_Ax2, gp_Dir, gp_Pln, gp_Pnt

from zencad.geom.shape import Shape as ResolvedShape

from ._value_operations import Vector3Value


def _angle_pair(value: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, tuple):
        return value
    return (-value / 2, value / 2)


def box(
    size: Vector3Value,
    center: bool | str | None,
) -> ResolvedShape:
    origin = gp_Pnt(0, 0, 0)
    if center is True:
        origin = gp_Pnt(-size.x / 2, -size.y / 2, -size.z / 2)
    elif isinstance(center, str):
        origin = gp_Pnt(
            -size.x / 2 if "x" in center else 0,
            -size.y / 2 if "y" in center else 0,
            -size.z / 2 if "z" in center else 0,
        )
    if center:
        axis = gp_Ax2(origin, gp_Dir(0, 0, 1))
        native = BRepPrimAPI_MakeBox(axis, size.x, size.y, size.z).Shape()
    else:
        native = BRepPrimAPI_MakeBox(size.x, size.y, size.z).Shape()
    return ResolvedShape(native)


def sphere(
    radius: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    if yaw is None and pitch is None:
        native = BRepPrimAPI_MakeSphere(radius).Shape()
    elif yaw is None:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeSphere(radius, start, finish).Shape()
    elif pitch is None:
        native = BRepPrimAPI_MakeSphere(radius, yaw).Shape()
    else:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeSphere(radius, start, finish, yaw).Shape()
    return ResolvedShape(native)


def cylinder(
    radius: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    axis = gp_Ax2(
        gp_Pnt(0, 0, -height / 2 if center else 0),
        gp_Dir(0, 0, 1),
    )
    builder = (
        BRepPrimAPI_MakeCylinder(axis, radius, height, yaw)
        if yaw is not None
        else BRepPrimAPI_MakeCylinder(axis, radius, height)
    )
    return ResolvedShape(builder.Shape())


def cone(
    radius1: float,
    radius2: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    axis = gp_Ax2(
        gp_Pnt(0, 0, -height / 2 if center else 0),
        gp_Dir(0, 0, 1),
    )
    builder = (
        BRepPrimAPI_MakeCone(axis, radius1, radius2, height, yaw)
        if yaw is not None
        else BRepPrimAPI_MakeCone(axis, radius1, radius2, height)
    )
    return ResolvedShape(builder.Shape())


def torus(
    radius1: float,
    radius2: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    if yaw is None and pitch is None:
        native = BRepPrimAPI_MakeTorus(radius1, radius2).Shape()
    elif yaw is None:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeTorus(radius1, radius2, start, finish).Shape()
    elif pitch is None:
        native = BRepPrimAPI_MakeTorus(radius1, radius2, yaw).Shape()
    else:
        start, finish = _angle_pair(pitch)
        native = BRepPrimAPI_MakeTorus(radius1, radius2, start, finish, yaw).Shape()
    return ResolvedShape(native)


def halfspace() -> ResolvedShape:
    face = BRepLib_MakeFace(gp_Pln()).Face()
    return ResolvedShape(BRepPrimAPI_MakeHalfSpace(face, gp_Pnt(0, 0, -1)).Solid())


def make_solid(shells: tuple[ResolvedShape, ...]) -> ResolvedShape:
    builder = BRepBuilderAPI_MakeSolid()
    for shell in shells:
        builder.Add(shell.Shell())
    fixer = ShapeFix_Solid(builder.Solid())
    fixer.Perform()
    return ResolvedShape(fixer.Solid())
