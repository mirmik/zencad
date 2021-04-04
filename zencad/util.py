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

from zencad.geombase import *


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
