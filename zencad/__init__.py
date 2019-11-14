import math
print("a")
import pyservoce
print("a")
from pyservoce import unify
print("a")
from pyservoce import point3, vector3
print("a")
from pyservoce import Scene, View, Color
print("a")
from pyservoce import Color as color
print("a")
from pyservoce import point3 as point
print("a")
from pyservoce import vector3 as vector
print("a")

from zencad.visual import screen
print("a")
from zencad.transform import *
print("a")

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
print("a")
from zencad.lazifier import disable_cache, test_mode
print("a")
import evalcache
print("a")

from zencad.util import deg, angle_pair, points, vectors
print("a")
from zencad.convert import *
print("a")
import types
print("a1")

moduledir = os.path.dirname(__file__)
print("a2")
exampledir = os.path.join(os.path.dirname(__file__), "examples")
print("a3")

from zencad.showapi import show, display, disp, hl, highlight
print("a4")

from zencad.geom.prim3d import *
print("a5")
from zencad.geom.prim2d import *
print("a6")
from zencad.geom.prim1d import *
print("a")

from zencad.geom.ops3d import *
print("a")
from zencad.geom.ops1d2d import *
print("a")

from zencad.showapi import default_scene
print("a")

#__DEFAULT_TRACE__ = True
#
#def enable_trace(en):
#    #import zencad.__main__
#    zencad.gui.application.__TRACED__ = en
#    zencad.gui.retransler.__RETRANSLER_TRACE__ = en
#    zencad.gui.mainwindow.__TRACE__ = en
#
#enable_trace(__DEFAULT_TRACE__)

print("a")
def gr(grad):
    print("'gr' function is deprecated. Use 'deg' instead")
    return float(grad) / 180.0 * math.pi


print("a")
def enable_cache_diagnostic():
    evalcache.diagnostic = True


print("a")
@lazy.lazy(cls=shape_generator)
def near_edge(shp, pnt):
    """Find near edge to point `pnt` in shape `shp`"""
    return pyservoce.near_edge(shp, pnt)


print("a")
@lazy.lazy(cls=shape_generator)
def near_face(shp, pnt):
    """Find near face to point `pnt` in shape `shp`"""
    return pyservoce.near_face(shp, pnt)


print("a")
@lazy
def near_vertex(shp, pnt):
    """Find near vertex to point `pnt` in shape `shp`
    Return vertex as point.
    """
    return pyservoce.near_vertex(shp, pnt).vertices()[0]


print("a")
@lazy.lazy(cls=shape_generator)
def near_vertex_shape(shp, pnt):
    """Find near vertex to point `pnt` in shape `shp`
    Return vertex as vertex shape.
    """
    return pyservoce.near_vertex(shp, pnt)


print("a")
@lazy.lazy(cls=shape_generator)
def unify(shp):
    return pyservoce.unify(shp)


print("a")
zencad.color = pyservoce.color

print("a")
zencad.color.white =     zencad.color(1,1,1)
print("a")
zencad.color.black =     zencad.color(0,0,0)
zencad.color.red =       zencad.color(1,0,0)
zencad.color.green =     zencad.color(0,1,0)
zencad.color.blue =      zencad.color(0,0,1)
zencad.color.yellow =    zencad.color(1,1,0)
zencad.color.magenta =   zencad.color(0,1,1)
zencad.color.cian =      zencad.color(1,0,1)
zencad.color.mech =      zencad.color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.color(0.6, 0.6, 0.8, 0.8)

print("a")
default_color = zencad.settings.Settings.get_default_color()


print("a")
pyservoce.Shape.move = pyservoce.Shape.translate
pyservoce.Shape.moveX = pyservoce.Shape.right
pyservoce.Shape.moveY = pyservoce.Shape.forw
pyservoce.Shape.moveZ = pyservoce.Shape.up

print("a")
zencad.move = zencad.translate
zencad.moveX = zencad.right
zencad.moveY = zencad.forw
zencad.moveZ = zencad.up


print("a")
def to_vector(arg):
    return zencad.util.vector3(arg)

def to_point(arg):
    return zencad.util.point3(arg)