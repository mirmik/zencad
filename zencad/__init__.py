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

from zencad.showapi import default_scene

from zencad.geom.curve3 import extract_curve

#__DEFAULT_TRACE__ = True
#
#def enable_trace(en):
#    #import zencad.__main__
#    zencad.gui.application.__TRACED__ = en
#    zencad.gui.retransler.__RETRANSLER_TRACE__ = en
#    zencad.gui.mainwindow.__TRACE__ = en
#
#enable_trace(__DEFAULT_TRACE__)

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


zencad.color = pyservoce.color

zencad.color.white =     zencad.color(1,1,1)
zencad.color.black =     zencad.color(0,0,0)
zencad.color.red =       zencad.color(1,0,0)
zencad.color.green =     zencad.color(0,1,0)
zencad.color.blue =      zencad.color(0,0,1)
zencad.color.yellow =    zencad.color(1,1,0)
zencad.color.magenta =   zencad.color(0,1,1)
zencad.color.cian =      zencad.color(1,0,1)
zencad.color.mech =      zencad.color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.color(0.6, 0.6, 0.8, 0.8)
zencad.color.orange =    zencad.color(1, 0xa5/255, 0)

default_color = zencad.settings.Settings.get_default_color()


pyservoce.Shape.move = pyservoce.Shape.translate
pyservoce.Shape.moveX = pyservoce.Shape.right
pyservoce.Shape.moveY = pyservoce.Shape.forw
pyservoce.Shape.moveZ = pyservoce.Shape.up

zencad.move = zencad.translate
zencad.moveX = zencad.right
zencad.moveY = zencad.forw
zencad.moveZ = zencad.up

def to_vector(arg):
    return zencad.util.vector3(arg)

def to_point(arg):
    return zencad.util.point3(arg)