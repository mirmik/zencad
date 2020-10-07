import math

try:
    import pyservoce
except Exception as ex:
    print(ex)
    raise ex

from pyservoce import unify
from pyservoce import point3, vector3
from pyservoce import Scene, View, Color
from pyservoce import Color as color
from zencad.util import point3 as point
from zencad.util import vector3 as vector
from zencad.libs.screw import screw

from zencad.visual import screen
from zencad.geom.transform import *

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.lazifier import disable_cache, test_mode
import evalcache

from zencad.util import *
from zencad.util2 import *
from zencad.convert.api import *
import types

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")

from zencad.showapi import show, display, disp, hl, highlight

from zencad.geom.prim3d import *
from zencad.geom.prim2d import *
from zencad.geom.prim1d import *
from zencad.geom.ops3d import *
from zencad.geom.ops1d2d import *
from zencad.showapi import default_scene
from zencad.geom.curve3 import extract_curve
from zencad.version import __version__

from zencad.platonic import *

import zencad.reflect 

class interactive_object(pyservoce.interactive_object):
    def __init__(self, obj, color=None):
        if color == None:
            color = zencad.default_color
            
        super().__init__(
            evalcache.unlazy_if_need(obj), 
            pyservoce.color(color)
        )
        self.object = obj


def gr(grad):
    print("'gr' function is deprecated. Use 'deg' instead")
    return float(grad) / 180.0 * math.pi


def enable_cache_diagnostic():
    evalcache.diagnostic = True


@lazy.lazy(cls=shape_generator)
def near_edge(shp, pnt):
    """Find near edge to point `pnt` in shape `shp`"""
    return pyservoce.near_edge(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_face(shp, pnt):
    """Find near face to point `pnt` in shape `shp`"""
    return pyservoce.near_face(shp, pnt)


@lazy
def near_vertex(shp, pnt):
    """Find near vertex to point `pnt` in shape `shp`
    Return vertex as point.
    """
    return pyservoce.near_vertex(shp, pnt).vertices()[0]


@lazy.lazy(cls=shape_generator)
def near_vertex_shape(shp, pnt):
    """Find near vertex to point `pnt` in shape `shp`
    Return vertex as vertex shape.
    """
    return pyservoce.near_vertex(shp, pnt)


@lazy.lazy(cls=shape_generator)
def unify(shp):
    return pyservoce.unify(shp)

@lazy
def triangulate(shp, defl):
    return pyservoce.triangulation(shp, defl)


zencad.color = pyservoce.color

zencad.color.white =     zencad.color(1,1,1)
zencad.color.black =     zencad.color(0,0,0)
zencad.color.red =       zencad.color(1,0,0)
zencad.color.green =     zencad.color(0,1,0)
zencad.color.blue =      zencad.color(0,0,1)
zencad.color.yellow =    zencad.color(1,1,0)
zencad.color.magenta =   zencad.color(1,0,1)
zencad.color.cian =      zencad.color(0,1,1)
zencad.color.mech =      zencad.color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.color(0.6, 0.6, 0.8, 0.8)
zencad.color.orange =    zencad.color(1, 0xa5/255, 0)

default_color = zencad.settings.Settings.get_default_color()


#pyservoce.Shape.move = pyservoce.Shape.translate
#pyservoce.Shape.moveX = pyservoce.Shape.right
#pyservoce.Shape.moveY = pyservoce.Shape.forw
#pyservoce.Shape.moveZ = pyservoce.Shape.up

zencad.move = zencad.translate
zencad.moveX = zencad.right
zencad.moveY = zencad.forw
zencad.moveZ = zencad.up

def to_vector(arg):
    return zencad.util.vector3(arg)

def to_point(arg):
    return zencad.util.point3(arg)

def wire_edges_orientation(edges):
    pairs = [ e.endpoints() for e in edges ]

    reverse = [False] * len(pairs) 
    for i in range(len(edges) - 1):
        if pairs[i][0].early(pairs[i+1][0]):
            reverse[i] = True
            reverse[i+1] = False
        elif pairs[i][0].early(pairs[i+1][1]):
            reverse[i] = True
            reverse[i+1] = True
        elif pairs[i][1].early(pairs[i+1][0]):
            reverse[i] = False
            reverse[i+1] = False
        elif pairs[i][1].early(pairs[i+1][1]):
            reverse[i] = False
            reverse[i+1] = True

    return zip(edges, reverse)

def sort_wire_edges(edges):
    res = []

    res.append(edges[0])

    lst = list(edges)
    del lst[0]
    
    while len(lst) > 0:
        ls, lf = res[-1].endpoints()
        for i in range(len(lst)):
            s, f = lst[i].endpoints()
            if s.early(ls) or s.early(lf) or f.early(ls) or f.early(lf):
                res.append(lst[i])
                del lst[i]
                break

    return res


def sort_wires_by_face_area(cycles):
    return sorted(cycles, key=lambda c: c.fill().mass(), reverse=True)

from zencad.geom.wire_builder import wire_builder
#import zencad.bullet