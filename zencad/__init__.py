import math

import pyservoce
from pyservoce import unify
from pyservoce import point3, vector3
from pyservoce import Scene, View, Color
from pyservoce import Color as color
from pyservoce import point3 as point
from pyservoce import vector3 as vector

from zencad.visual import screen
from zencad.transform import *

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.lazifier import disable_cache, test_mode
import evalcache

from zencad.util import deg, angle_pair, points, vectors
from zencad.convert import *
import types

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")

from zencad.showapi import show, display, disp, hl, highlight

from zencad.geom.prim3d import *
from zencad.geom.prim2d import *
from zencad.geom.prim1d import *

from zencad.geom.ops3d import *
from zencad.geom.ops1d2d import *

def gr(grad):
    print("'gr' function is deprecated. Use 'deg' instead")
    return float(grad) / 180.0 * math.pi


def enable_cache_diagnostic():
    evalcache.diagnostic = True


@lazy.lazy(cls=shape_generator)
def near_edge(*args, **kwargs):
    return pyservoce.near_edge(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def near_face(*args, **kwargs):
    return pyservoce.near_face(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def near_vertex(*args, **kwargs):
    return pyservoce.near_vertex(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def unify(shp):
    return pyservoce.unify(shp)
