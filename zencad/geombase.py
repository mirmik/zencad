import math
import os
import numpy
import sys

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_XYZ, gp_Quaternion
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCC.Core.Geom import Geom_CartesianPoint

import zencad.geom.transformable
import evalcache


class xyz(numpy.ndarray, zencad.geom.transformable.Transformable):
    def __new__(cls, *args, info=None):
        args = [evalcache.unlazy_if_need(a) for a in args]

        if len(args) == 0:
            input_array = (0, 0, 0)

        elif isinstance(args[0], TopoDS_Vertex):
            pnt = BRep_Tool.Pnt(args[0])
            input_array = (pnt.X(), pnt.Y(), pnt.Z())

        elif isinstance(args[0], (gp_Pnt, gp_Dir, gp_Vec, gp_XYZ)):
            input_array = (args[0].X(), args[0].Y(), args[0].Z())
        else:
            try:
                _ = args[0][0]
                input_array = args[0]
            except:
                input_array = args

        if len(input_array) == 1:
            input_array = ((input_array[0], 0, 0))
        elif len(input_array) == 2:
            input_array = ((input_array[0], input_array[1], 0))
        elif len(input_array) == 3:
            input_array = ((input_array[0], input_array[1], input_array[2]))

        obj = numpy.asarray(input_array).view(cls)
        obj.info = info
        return obj

    @property
    def x(self): return float(self[0])
    @property
    def y(self): return float(self[1])
    @property
    def z(self): return float(self[2])

    def __lt__(self, oth):
        if self.x < oth.x:
            return True
        if self.x > oth.x:
            return False
        if self.y < oth.y:
            return True
        if self.y > oth.y:
            return False
        if self.z < oth.z:
            return True
        if self.z > oth.z:
            return False
        return False

    def __gt__(self, oth):
        if self.x > oth.x:
            return True
        if self.x < oth.x:
            return False
        if self.y > oth.y:
            return True
        if self.y < oth.y:
            return False
        if self.z > oth.z:
            return True
        if self.z < oth.z:
            return False
        return False

    def Pnt(self):
        return gp_Pnt(float(self[0]), float(self[1]), float(self[2]))

    def Vec(self):
        return gp_Vec(float(self[0]), float(self[1]), float(self[2]))

    def Vtx(self):
        return to_Vertex(self)

    def to_tuple(self):
        return (self.x, self.y, self.z)

    def cross(self, oth):
        return vector3(numpy.cross(self, oth))

    def early(self, oth):
        return (
            abs(self.x - oth.x) < 1e-5 and
            abs(self.y - oth.y) < 1e-5 and
            abs(self.z - oth.z) < 1e-5
        )

    def __add__(self, oth):
        return point3(self[0] + oth[0], self[1] + oth[1], self[2] + oth[2])

    def __sub__(self, oth):
        return point3(self[0] - oth[0], self[1] - oth[1], self[2] - oth[2])

    def __eq__(self, oth):
        return self.x == oth.x and self.y == oth.y and self.z == oth.z

    def __ne__(self, oth):
        return self.x != oth.x or self.y != oth.y or self.z != oth.z

    def __mul__(self, m):
        return point3(self.x * m, self.y * m, self.z * m)

    def __div__(self, m):
        return point3(self.x / m, self.y / m, self.z / m)

    def __round__(self, r):
        return point3(round(self.x, r), round(self.y, r), round(self.z, r))

    def __str__(self):
        return f"point3({self.x},{self.y},{self.z})"

    def __repr__(self):
        return f"point3({self.x},{self.y},{self.z})"

    def distance(self, oth):
        diff = self - oth
        return numpy.linalg.norm(diff)

    def angle(self, oth):
        oth = vector3(oth)
        a = self.to_unit_vector()
        b = oth.to_unit_vector()

        dot = numpy.dot(a, b)
        angle = math.acos(dot)

        return angle

    def to_vector3(self):
        return vector3(*self)

    def to_point3(self):
        return point3(*self)

    def to_unit_vector(self):
        norm = numpy.linalg.norm(self)
        return self / norm


class point3(xyz):
    def transform(self, trsf):
        t = trsf._trsf
        return point3(self.Pnt().Transformed(t))


class vector3(xyz):
    def transform(self, trsf):
        t = trsf._trsf
        return vector3(self.Vec().Transformed(t))

    def cross(self, oth):
        return vector3(numpy.cross(self, oth))

    def normalize(self):
        n = numpy.linalg.norm(self)
        return vector3(self / n)


class quat:
    def __init__(self, arg):
        if isinstance(arg, gp_Quaternion):
            self.x = arg.X()
            self.y = arg.Y()
            self.z = arg.Z()
            self.w = arg.W()
        else:
            NotImplemented()


def points(pnts):
    return [point3(item) for item in pnts]


def points2(tpls):
    return [points(t) for t in tpls]


def vectors(pnts):
    return [vector3(item) for item in pnts]


def to_numpy(arg):
    if isinstance(arg, (gp_Vec, gp_Pnt, gp_Dir)):
        return numpy.array([arg.X(), arg.Y(), arg.Z()])
    elif isinstance(arg, (TopoDS_Vertex)):
        arg = BRep_Tool.Pnt(arg)
        return numpy.array([arg.X(), arg.Y(), arg.Z()])
    else:
        raise Exception("unresolved type", arg.__class__)


def to_Pnt(arg):
    if len(arg) == 2:
        return gp_Pnt(float(arg[0]), float(arg[1]), 0)
    else:
        return gp_Pnt(float(arg[0]), float(arg[1]), float(arg[2]))


def to_Vec(arg):
    if arg is None:
        return gp_Vec(0, 0, 0)
    if len(arg) == 2:
        return gp_Vec(float(arg[0]), float(arg[1]), 0)
    return gp_Vec(float(arg[0]), float(arg[1]), float(arg[2]))


def to_Vertex(arg):
    return BRepBuilderAPI_MakeVertex(to_Pnt(arg)).Vertex()


def to_GeomPoint(arg):
    return Geom_CartesianPoint(to_Pnt(arg))
