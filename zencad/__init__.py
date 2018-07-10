import evalcache

import math
import hashlib
import pyservoce
from pyservoce import Scene, point3, Color

evalcache.enable()

ShapeWrap = evalcache.create_class_wrap("ShapeWrap", wrapclass = pyservoce.Shape)
ShapeWrap.__wrapmethod__("__add__", ShapeWrap, pyservoce.Shape.__add__)
ShapeWrap.__wrapmethod__("__sub__", ShapeWrap, pyservoce.Shape.__sub__)
ShapeWrap.__wrapmethod__("__xor__", ShapeWrap, pyservoce.Shape.__xor__)
ShapeWrap.__wrapmethod__("up", ShapeWrap, pyservoce.Shape.up)
ShapeWrap.__wrapmethod__("down", ShapeWrap, pyservoce.Shape.down)
ShapeWrap.__wrapmethod__("right", ShapeWrap, pyservoce.Shape.right)
ShapeWrap.__wrapmethod__("left", ShapeWrap, pyservoce.Shape.left)
ShapeWrap.__wrapmethod__("forw", ShapeWrap, pyservoce.Shape.forw)
ShapeWrap.__wrapmethod__("back", ShapeWrap, pyservoce.Shape.back)
ShapeWrap.__wrapmethod__("rotateX", ShapeWrap, pyservoce.Shape.rotateX)
ShapeWrap.__wrapmethod__("rotateY", ShapeWrap, pyservoce.Shape.rotateY)
ShapeWrap.__wrapmethod__("rotateZ", ShapeWrap, pyservoce.Shape.rotateZ)
ShapeWrap.__wrapmethod__("mirrorXY", ShapeWrap, pyservoce.Shape.mirrorXY)
ShapeWrap.__wrapmethod__("mirrorYZ", ShapeWrap, pyservoce.Shape.mirrorYZ)
ShapeWrap.__wrapmethod__("mirrorXZ", ShapeWrap, pyservoce.Shape.mirrorXZ)
ShapeWrap.__wrapmethod__("translate", ShapeWrap, pyservoce.Shape.translate)
ShapeWrap.__wrapmethod__("transform", ShapeWrap, pyservoce.Shape.transform)
ShapeWrap.__wrapmethod__("fillet", ShapeWrap, pyservoce.Shape.fillet)

def point3_hash(pnt):
	m = hashlib.sha1()
	m.update(str(pnt.x).encode("utf-8"))
	m.update(str(pnt.y).encode("utf-8"))
	m.update(str(pnt.z).encode("utf-8"))
	return m.digest()

def transform_hash(trsf):
	return "afsadfsadgasgsdfg".encode("utf-8")

evalcache.hashfuncs[pyservoce.point3] = point3_hash
#evalcache.hashfuncs[pyservoce.translate] = transform_hash
#evalcache.hashfuncs[pyservoce.plane_mirror] = transform_hash
#evalcache.hashfuncs[pyservoce.complex_transformation] = transform_hash

#ShapeSweepWrap = evalcache.create_class_wrap("ShapeSweepWrap", pyservoce.ShapeSweep, ShapeWrap)

#print(pyservoce.Shape.__dict__)
#pyservoce.Shape.left = evalcache.FunctionHeader(Shape.left)
#pyservoce.Shape.translate = evalcache.FunctionHeader(Shape.translate)

#print(pyservoce.Shape.__dict__)

def solid_or_face(arr):
	if isinstance(arr[0], ShapeWrap): return ShapeWrap
	if isinstance(arr[0], ShapeWrap): return ShapeWrap
	print("???")
	exit(-1)

@evalcache.lazy(solid_or_face)
def union(arr): return pyservoce.make_union(arr)

@evalcache.lazy(solid_or_face)
def difference(arr): return pyservoce.make_difference(arr)

@evalcache.lazy(solid_or_face)
def intersect(arr): return pyservoce.make_intersect(arr)

def points(tpls):
	return [ point3(*t) for t in tpls ]

def vectors(tpls):
	return [ pyservoce.vector3(*t) for t in tpls ]

def to_vector3(v):
	try:
		if isinstance(v, pyservoce.vector3):
			return v
		return pyservoce.vector3(v[0], v[1], v[2])
	except Exception:
		return pyservoce.vector3(0,0,v)


def enable_cache(arg):
	print("Warn: cache in rework state. comming soon.")

#display
default_scene = Scene()

def display(shp):
	if isinstance(shp, evalcache.LazyObject):
		default_scene.add(shp.eval())
	else:
		default_scene.add(shp)

def show(scn = default_scene):
	pyservoce.display_scene(scn)

#prim3d
@evalcache.lazy(ShapeWrap)
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return pyservoce.make_box(size[0], size[1], size[2], center)
		else:
			return pyservoce.make_box(size, size, size, center)
	else:
		return pyservoce.make_box(size, arg2, arg3, center)

@evalcache.lazy(ShapeWrap)
def sphere(r): 
	return pyservoce.make_sphere(r)

@evalcache.lazy(ShapeWrap)
def cylinder(r, h, center = False): 
	return pyservoce.make_cylinder(r,h,center)

@evalcache.lazy(ShapeWrap)
def cone(r1, r2, h, center = False): 
	return pyservoce.make_cone(r1,r2,h,center)

@evalcache.lazy(ShapeWrap)
def torus(r1, r2): 
	return pyservoce.make_torus(r1,r2)

#sweep
@evalcache.lazy(ShapeWrap)
def linear_extrude(shp, vec, center = False):
	return pyservoce.make_linear_extrude(shp, to_vector3(vec), center)

@evalcache.lazy(ShapeWrap)
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@evalcache.lazy(ShapeWrap)
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

#face
@evalcache.lazy(ShapeWrap)
def circle(r):
	return pyservoce.make_circle(r)

@evalcache.lazy(ShapeWrap)
def ngon(r, n):
	return pyservoce.make_ngon(r, n)

@evalcache.lazy(ShapeWrap)
def polygon(pnts):
	return pyservoce.make_polygon(pnts)

@evalcache.lazy(ShapeWrap)
def square(a, center = False):
	return pyservoce.make_square(a, center)

@evalcache.lazy(ShapeWrap)
def rectangle(a, b, center = False):
	return pyservoce.make_rectangle(a, b, center)

#wire
def segment(*args, **kwargs):
	return pyservoce.make_segment(*args, **kwargs)

def polysegment(*args, **kwargs):
	return pyservoce.make_polysegment(*args, **kwargs)

def wcircle(*args, **kwargs):
	return pyservoce.make_wcircle(*args, *kwargs)

def interpolate(*args, **kwargs):
	return pyservoce.make_interpolate(*args, **kwargs)

def complex_wire(*args, **kwargs):
	return pyservoce.make_complex_wire(*args, **kwargs)

@evalcache.lazy(ShapeWrap)
def sweep(prof, path):
	return pyservoce.make_sweep(prof, path)



def helix(*args, **kwargs):
	#return make_helix(*args, **kwargs)
	return pyservoce.make_long_helix(*args, **kwargs)


##widget
#from zencad.widget import display
#from zencad.widget import show
#
##cache
#from zencad.cache import enable as enable_cache
#
##solid
#from zencad.solid import box
#from zencad.solid import sphere
#from zencad.solid import torus
#from zencad.solid import cylinder
#from zencad.solid import cone
#
#from zencad.solid import linear_extrude
#from zencad.solid import pipe
#
##face
#from zencad.face import circle
#from zencad.face import ngon
#from zencad.face import square
#from zencad.face import rectangle
#from zencad.face import polygon
#
##wire
#from zencad.wire import segment
#from zencad.wire import polysegment
#from zencad.wire import circle as wcircle
#from zencad.wire import arc_by_points
#from zencad.wire import interpolate
#
##boolops
#from zencad.boolops import union
#from zencad.boolops import difference
#from zencad.boolops import intersect
#
#def error(str):
#	print("ZenCadError: " + str)
#	exit(-1)
#
#from zencad.math3 import vector
#from zencad.math3 import vector as vec
#from zencad.math3 import vectors
#
#from zencad.math3 import point
#from zencad.math3 import point as pnt
#from zencad.math3 import points
#
##from pyservoce import ZenVertex as vertex
#
def gr(grad): return float(grad) / 180.0 * math.pi
def deg(grad): return float(grad) / 180.0 * math.pi
#from zencad.math3 import point as pnt
#
#
#
#
#from pyservoce import scene
#from pyservoce import camera
#from pyservoce import view

def trans_type(obj, arg):
	if (isinstance(arg, ShapeWrap)): return ShapeWrap
	if (isinstance(arg, ShapeWrap)): return ShapeWrap
	print("???2")
	exit(-1)

TransformWrap = evalcache.create_class_wrap("TransformWrap", wrapclass = pyservoce.transformation)
TransformWrap .__wrapmethod__("__mul__", TransformWrap, pyservoce.transformation.__mul__ )
TransformWrap .__wrapmethod__("__call__", trans_type, pyservoce.transformation.__call__ )

@evalcache.lazy(TransformWrap)
def translate(*args, **kwargs): return pyservoce.translate(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateX(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateY(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateZ(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorXZ(*args, **kwargs): return pyservoce.mirrorXZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorYZ(*args, **kwargs): return pyservoce.mirrorYZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorXY(*args, **kwargs): return pyservoce.mirrorXY(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorX(*args, **kwargs): return pyservoce.mirrorX(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorY(*args, **kwargs): return pyservoce.mirrorY(*args, **kwargs)

@evalcache.lazy(TransformWrap)
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