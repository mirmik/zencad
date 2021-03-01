import math
import os
import numpy
import sys

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCC.Core.Geom import Geom_CartesianPoint

import zencad.geom.transformable
import evalcache


def as_indexed(arg):
    if len(arg) != 1:
        return tuple(arg)
    return arg


def deg(grad):
    return float(grad) / 180.0 * math.pi


def deg2rad(d):
    return deg(d)


def rad2deg(d):
    return float(d) * 180.0 / math.pi


def angle_pair(arg):
    if isinstance(arg, tuple) or isinstance(arg, list):
        return arg

    if (arg >= 0):
        return (0, arg)
    else:
        return (arg, 0)


class point3(numpy.ndarray, zencad.geom.transformable.Transformable):
    def __new__(cls, *args, info=None):
        if isinstance(args[0], (gp_Pnt, gp_Dir, gp_Vec)):
            input_array = (args[0].X(), args[0].Y(), args[0].Z())

        elif hasattr(args[0], "__getitem__"):
            input_array = args[0]
        else:
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

    def Vtx(self):
        return to_Vertex(self)

    def to_tuple(self):
        return (self.x, self.y, self.z)

    def transform(self, trsf):
        t = trsf._trsf
        return point3(self.Pnt().Transformed(t))

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


class vector3(numpy.ndarray, zencad.geom.transformable.Transformable):
    def __new__(cls, *args, info=None):
        args = [evalcache.unlazy_if_need(a) for a in args]
        if isinstance(args[0], (gp_Pnt, gp_Dir, gp_Vec)):
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

    def __eq__(self, oth):
        return self.x == oth.x and self.y == oth.y and self.z == oth.z

    def __ne__(self, oth):
        return self.x != oth.x or self.y != oth.y or self.z != oth.z

    def __mul__(self, m):
        return point3(self.x * m, self.y * m, self.z * m)

    def __div__(self, m):
        return point3(self.x / m, self.y / m, self.z / m)

    def Vec(self):
        return gp_Vec(float(self[0]), float(self[1]), float(self[2]))

    def transform(self, trsf):
        t = trsf._trsf
        return point3(self.Pnt().Transformed(t))

    def cross(self, oth):
        return vector3(numpy.cross(self, oth))

    def normalize(self):
        n = numpy.linalg.norm(self)
        return vector3(self / n)


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
    return gp_Vec(float(arg[0]), float(arg[1]), float(arg[2]))


def to_Vertex(arg):
    return BRepBuilderAPI_MakeVertex(to_Pnt(arg)).Vertex()


def to_GeomPoint(arg):
    return Geom_CartesianPoint(to_Pnt(arg))


def examples_paths(root=None):
    import zencad
    ret = []

    if root is None:
        root = os.path.join(zencad.moduledir, "examples")
    else:
        root = os.path.abspath(root)

    for path, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if not d.startswith('__pycache__')]
        for name in files:
            if os.path.splitext(name)[1] == ".py":
                ret.append(os.path.join(path, name))

    return ret


def examples_dict(root=None):
    import zencad
    if root is None:
        root = os.path.join(zencad.moduledir, "examples")

    dct = {}
    dct["__files__"] = set()

    for d in os.listdir(root):
        dpath = os.path.join(root, d)

        if d == "__pycache__" or d == "fonts":
            continue

        if os.path.isdir(dpath):
            dct[d] = examples_dict(dpath)
        else:
            dct["__files__"].add(d)

    return dct
