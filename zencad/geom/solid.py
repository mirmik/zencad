from zencad.geom.shape import Shape, nocached_shape_generator, shape_generator
from zencad.util import as_indexed, angle_pair
import OCC.Core.BRepPrimAPI
from OCC.Core.gp import gp_Ax2, gp_Pnt, gp_Vec, gp_Dir, gp_Pln
from OCC.Core.BRepLib import BRepLib_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeHalfSpace
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.ShapeFix import ShapeFix_Solid

from zencad.lazifier import *


def _box(size, y=None, z=None, center=None):
    if isinstance(size, (float, int)):
        x = size
        if y is None and z is None:
            size = (x, x, x)
        else:
            if z is None:
                size = (x, y, 0)
            else:
                size = (x, y, z)

    x, y, z = size[0], size[1], size[2]

    if center:
        ax2 = gp_Ax2(gp_Pnt(-x / 2, -y / 2, -z / 2), gp_Dir(0, 0, 1))
        return Shape(OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(ax2, *size).Shape())
    else:
        return Shape(OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(*size).Shape())


def _cube(size, y=None, z=None, center=None):
    return _box(size, y, z, center)


def _sphere(r, yaw=None, pitch=None):
    if yaw is None and pitch is None:
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeSphere(r).Shape()
    elif yaw is None and pitch is not None:
        pitch = angle_pair(pitch)
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeSphere(
            r, pitch[0], pitch[1]).Shape()
    elif yaw is not None and pitch is None:
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeSphere(r, yaw).Shape()
    else:
        pitch = angle_pair(pitch)
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeSphere(
            r, pitch[0], pitch[1], yaw).Shape()

    return Shape(raw)


def _cylinder(r, h, yaw=None, center=False):
    if yaw:
        if center:
            ax2 = gp_Ax2(gp_Pnt(0, 0, -h/2), gp_Dir(0, 0, 1))
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCylinder(
                ax2, r, h, yaw).Shape()
            return Shape(raw)
        else:
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCylinder(
                r, h, yaw).Shape()
            return Shape(raw)
    else:
        if center:
            ax2 = gp_Ax2(gp_Pnt(0, 0, -h/2), gp_Dir(0, 0, 1))
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCylinder(
                ax2, r, h).Shape()
            return Shape(raw)
        else:
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCylinder(r, h).Shape()
            return Shape(raw)


def _cone(r1, r2, h, yaw=None, center=False):
    if yaw:
        if center:
            ax2 = gp_Ax2(gp_Pnt(0, 0, -h / 2), gp_Dir(0, 0, 1))
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCone(
                ax2, r1, r2, h, yaw).Shape()
            return Shape(raw)
        else:
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCone(
                r1, r2, h, yaw).Shape()
            return Shape(raw)

    else:
        if center:
            ax2 = gp_Ax2(gp_Pnt(0, 0, -h / 2), gp_Dir(0, 0, 1))
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCone(
                ax2, r1, r2, h).Shape()
            return Shape(raw)
        else:
            raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCone(r1, r2, h).Shape()
            return Shape(raw)


def _torus(r1, r2, yaw=None, pitch=None):
    if yaw is None and pitch is None:
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeTorus(r1, r2).Shape()
    elif yaw is None and pitch is not None:
        pitch = angle_pair(pitch)
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeTorus(
            r1, r2, pitch[0], pitch[1]).Shape()
    elif yaw is not None and pitch is None:
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeTorus(r1, r2, yaw).Shape()
    else:
        pitch = angle_pair(pitch)
        raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeTorus(
            r1, r2, pitch[0], pitch[1], yaw).Shape()

    return Shape(raw)


def _halfspace():
    F = BRepLib_MakeFace(gp_Pln()).Face()
    MHS = BRepPrimAPI_MakeHalfSpace(F, gp_Pnt(0, 0, -1))
    return Shape(MHS.Solid())


@lazy.lazy(cls=nocached_shape_generator)
def box(size, y=None, z=None, center=None):
    return _box(size, y, z, center)


@lazy.lazy(cls=nocached_shape_generator)
def cube(size, y=None, z=None, center=None):
    return _cube(size, y, z, center)


@lazy.lazy(cls=nocached_shape_generator)
def sphere(r, yaw=None, pitch=None):
    return _sphere(r, yaw, pitch)


@lazy.lazy(cls=nocached_shape_generator)
def cylinder(r, h, yaw=None, center=False):
    return _cylinder(r, h, yaw, center)


@lazy.lazy(cls=nocached_shape_generator)
def cone(r1, r2, h, yaw=None, center=False):
    return _cone(r1, r2, h, yaw, center)


@lazy.lazy(cls=nocached_shape_generator)
def torus(r1, r2, yaw=None, pitch=None):
    return _torus(r1, r2, yaw=yaw, pitch=pitch)


@lazy.lazy(cls=nocached_shape_generator)
def halfspace():
    return _halfspace()


def _make_solid(shells):
    if not isinstance(shells, (list, tuple)):
        shells = [shells]

    algo = BRepBuilderAPI_MakeSolid()

    for s in shells:
        algo.Add(s.Shell())

    fixer = ShapeFix_Solid(algo.Solid())
    fixer.Perform()
    return Shape(fixer.Solid())


@lazy.lazy(cls=shape_generator)
def make_solid(shells):
    return _make_solid(shells)


def _nullshape():
    return _box(1, 1, 1) - _box(1, 1, 1)


@lazy.lazy(cls=nocached_shape_generator)
def nullshape():
    return _nullshape()
