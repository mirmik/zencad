import evalcache
import evalcache.dirdict

import math
import hashlib

import pyservoce
from pyservoce import Scene, point3, Color

lazy = evalcache.Lazy(cache = evalcache.dirdict.dirdict(".evalcache"), algo = hashlib.sha256)

@lazy
def union(arr): return pyservoce.make_union(arr)

@lazy
def difference(arr): return pyservoce.make_difference(arr)

@lazy
def intersect(arr): return pyservoce.make_intersect(arr)

def point3(*t):
	return pyservoce.point3(*t)

def vector3(*t):
	return pyservoce.vector3(*t)

def points(tpls):
	return [ pyservoce.point3(*t) for t in tpls ]

def vectors(tpls):
	return [ pyservoce.vector3(*t) for t in tpls ]

def to_vector3(v):
	try:
		if isinstance(v, pyservoce.vector3):
			return v
		return pyservoce.vector3(v[0], v[1], v[2])
	except Exception:
		return pyservoce.vector3(0,0,v)

##display
default_scene = Scene()

def display(shp):
	if isinstance(shp, evalcache.LazyObject):
		default_scene.add(evalcache.unlazy(shp))
	else:
		default_scene.add(shp)

def show(scn = default_scene):
	pyservoce.display_scene(scn)

##prim3d
@lazy
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return pyservoce.make_box(size[0], size[1], size[2], center)
		else:
			return pyservoce.make_box(size, size, size, center)
	else:
		return pyservoce.make_box(size, arg2, arg3, center)

#prim3d
@lazy
def sphere(r): 
	return pyservoce.make_sphere(r)

@lazy
def cylinder(r, h, center = False): 
	return pyservoce.make_cylinder(r,h,center)

@lazy
def cone(r1, r2, h, center = False): 
	return pyservoce.make_cone(r1,r2,h,center)

@lazy
def torus(r1, r2): 
	return pyservoce.make_torus(r1,r2)

@lazy
def linear_extrude(shp, vec, center = False):
	return pyservoce.make_linear_extrude(shp, to_vector3(vec), center)

@lazy
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@lazy
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

#face
@lazy
def circle(r):
	return pyservoce.make_circle(r)

@lazy
def ngon(r, n):
	return pyservoce.make_ngon(r, n)

@lazy
def polygon(pnts):
	return pyservoce.make_polygon(pnts)

@lazy
def square(a, center = False):
	return pyservoce.make_square(a, center)

@lazy
def rectangle(a, b, center = False):
	return pyservoce.make_rectangle(a, b, center)

#wire
@lazy
def segment(*args, **kwargs):
	return pyservoce.make_segment(*args, **kwargs)

@lazy
def polysegment(*args, **kwargs):
	return pyservoce.make_polysegment(*args, **kwargs)

@lazy
def wcircle(*args, **kwargs):
	return pyservoce.make_wcircle(*args, *kwargs)

@lazy
def interpolate(*args, **kwargs):
	return pyservoce.make_interpolate(*args, **kwargs)

@lazy
def complex_wire(*args, **kwargs):
	return pyservoce.make_complex_wire(*args, **kwargs)

@lazy
def sweep(prof, path):
	return pyservoce.make_sweep(prof, path)

@lazy
def helix(*args, **kwargs):
	#return make_helix(*args, **kwargs)
	return pyservoce.make_long_helix(*args, **kwargs)


###widget
##from zencad.widget import display
##from zencad.widget import show
##
###cache
##from zencad.cache import enable as enable_cache
##
###solid
##from zencad.solid import box
##from zencad.solid import sphere
##from zencad.solid import torus
##from zencad.solid import cylinder
##from zencad.solid import cone
##
##from zencad.solid import linear_extrude
##from zencad.solid import pipe
##
###face
##from zencad.face import circle
##from zencad.face import ngon
##from zencad.face import square
##from zencad.face import rectangle
##from zencad.face import polygon
##
###wire
##from zencad.wire import segment
##from zencad.wire import polysegment
##from zencad.wire import circle as wcircle
##from zencad.wire import arc_by_points
##from zencad.wire import interpolate
##
###boolops
##from zencad.boolops import union
##from zencad.boolops import difference
##from zencad.boolops import intersect
##
##def error(str):
##	print("ZenCadError: " + str)
##	exit(-1)
##
##from zencad.math3 import vector
##from zencad.math3 import vector as vec
##from zencad.math3 import vectors
##
##from zencad.math3 import point
##from zencad.math3 import point as pnt
##from zencad.math3 import points
##
###from pyservoce import ZenVertex as vertex
##

def gr(grad): 
	print("'gr' function is deprecated. Use 'deg' instead")
	return float(grad) / 180.0 * math.pi

def deg(grad): return float(grad) / 180.0 * math.pi

##from zencad.math3 import point as pnt
##
##
##
##
##from pyservoce import scene
##from pyservoce import camera
##from pyservoce import view
#
#def trans_type(obj, arg):
#	if (isinstance(arg, ShapeWrap)): return ShapeWrap
#	if (isinstance(arg, ShapeWrap)): return ShapeWrap
#	print("???2")
#	exit(-1)
#
#TransformWrap = evalcache.create_class_wrap("TransformWrap", wrapclass = pyservoce.transformation)
#TransformWrap .__wrapmethod__("__mul__", TransformWrap, pyservoce.transformation.__mul__ )
#TransformWrap .__wrapmethod__("__call__", trans_type, pyservoce.transformation.__call__ )
#
@lazy
def translate(*args, **kwargs): return pyservoce.translate(*args, **kwargs)

@lazy
def up(*args, **kwargs): return pyservoce.up(*args, **kwargs)

@lazy
def down(*args, **kwargs): return pyservoce.down(*args, **kwargs)

@lazy
def left(*args, **kwargs): return pyservoce.left(*args, **kwargs)

@lazy
def right(*args, **kwargs): return pyservoce.right(*args, **kwargs)

@lazy
def forw(*args, **kwargs): return pyservoce.forw(*args, **kwargs)

@lazy
def back(*args, **kwargs): return pyservoce.back(*args, **kwargs)

@lazy
def rotateX(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@lazy
def rotateY(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@lazy
def rotateZ(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@lazy
def mirrorXZ(*args, **kwargs): return pyservoce.mirrorXZ(*args, **kwargs)

@lazy
def mirrorYZ(*args, **kwargs): return pyservoce.mirrorYZ(*args, **kwargs)

@lazy
def mirrorXY(*args, **kwargs): return pyservoce.mirrorXY(*args, **kwargs)

@lazy
def mirrorX(*args, **kwargs): return pyservoce.mirrorX(*args, **kwargs)

@lazy
def mirrorY(*args, **kwargs): return pyservoce.mirrorY(*args, **kwargs)

@lazy
def mirrorZ(*args, **kwargs): return pyservoce.mirrorZ(*args, **kwargs)

class multitransform:
	def __init__(self, transes):
		self.transes = transes

	def __call__(self, shp):
		return union([t(shp) for t in self.transes])

def nulltrans(): return translate(0,0,0) 

def sqrtrans(): return multitransform([ 
	nulltrans(), 
	mirrorYZ(),
	mirrorXZ(), 
	mirrorZ() 
])