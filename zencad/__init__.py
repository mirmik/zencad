import evalcache

import math
import hashlib
import zencad.zenlib
from zencad.zenlib import Scene, point3, Color


SolidWrap = evalcache.create_class_wrap("SolidWrap", wrapclass = zencad.zenlib.Solid)
SolidWrap.__wrapmethod__("__add__", SolidWrap, zencad.zenlib.Solid.__add__)
SolidWrap.__wrapmethod__("__sub__", SolidWrap, zencad.zenlib.Solid.__sub__)
SolidWrap.__wrapmethod__("__xor__", SolidWrap, zencad.zenlib.Solid.__xor__)
SolidWrap.__wrapmethod__("up", SolidWrap, zencad.zenlib.Solid.up)
SolidWrap.__wrapmethod__("down", SolidWrap, zencad.zenlib.Solid.down)
SolidWrap.__wrapmethod__("right", SolidWrap, zencad.zenlib.Solid.right)
SolidWrap.__wrapmethod__("left", SolidWrap, zencad.zenlib.Solid.left)
SolidWrap.__wrapmethod__("forw", SolidWrap, zencad.zenlib.Solid.forw)
SolidWrap.__wrapmethod__("back", SolidWrap, zencad.zenlib.Solid.back)
SolidWrap.__wrapmethod__("rotateX", SolidWrap, zencad.zenlib.Solid.rotateX)
SolidWrap.__wrapmethod__("rotateY", SolidWrap, zencad.zenlib.Solid.rotateY)
SolidWrap.__wrapmethod__("rotateZ", SolidWrap, zencad.zenlib.Solid.rotateZ)
SolidWrap.__wrapmethod__("mirrorXY", SolidWrap, zencad.zenlib.Solid.mirrorXY)
SolidWrap.__wrapmethod__("mirrorYZ", SolidWrap, zencad.zenlib.Solid.mirrorYZ)
SolidWrap.__wrapmethod__("mirrorXZ", SolidWrap, zencad.zenlib.Solid.mirrorXZ)
SolidWrap.__wrapmethod__("translate", SolidWrap, zencad.zenlib.Solid.translate)
SolidWrap.__wrapmethod__("transform", SolidWrap, zencad.zenlib.Solid.transform)
SolidWrap.__wrapmethod__("fillet", SolidWrap, zencad.zenlib.Solid.fillet)

#SolidSweepWrap = evalcache.create_class_wrap("SolidSweepWrap", zencad.zenlib.SolidSweep, SolidWrap)

FaceWrap = evalcache.create_class_wrap("FaceWrap", wrapclass = zencad.zenlib.Face)
FaceWrap.__wrapmethod__("__add__", FaceWrap, zencad.zenlib.Face.__add__)
FaceWrap.__wrapmethod__("__sub__", FaceWrap, zencad.zenlib.Face.__sub__)
FaceWrap.__wrapmethod__("__xor__", FaceWrap, zencad.zenlib.Face.__xor__)
FaceWrap.__wrapmethod__("up", FaceWrap, zencad.zenlib.Face.up)
FaceWrap.__wrapmethod__("down", FaceWrap, zencad.zenlib.Face.down)
FaceWrap.__wrapmethod__("right", FaceWrap, zencad.zenlib.Face.right)
FaceWrap.__wrapmethod__("left", FaceWrap, zencad.zenlib.Face.left)
FaceWrap.__wrapmethod__("forw", FaceWrap, zencad.zenlib.Face.forw)
FaceWrap.__wrapmethod__("back", FaceWrap, zencad.zenlib.Face.back)
FaceWrap.__wrapmethod__("rotateX", FaceWrap, zencad.zenlib.Face.rotateX)
FaceWrap.__wrapmethod__("rotateY", FaceWrap, zencad.zenlib.Face.rotateY)
FaceWrap.__wrapmethod__("rotateZ", FaceWrap, zencad.zenlib.Face.rotateZ)
FaceWrap.__wrapmethod__("mirrorXY", FaceWrap, zencad.zenlib.Face.mirrorXY)
FaceWrap.__wrapmethod__("mirrorYZ", FaceWrap, zencad.zenlib.Face.mirrorYZ)
FaceWrap.__wrapmethod__("mirrorXZ", FaceWrap, zencad.zenlib.Face.mirrorXZ)
FaceWrap.__wrapmethod__("translate", FaceWrap, zencad.zenlib.Face.translate)
FaceWrap.__wrapmethod__("transform", FaceWrap, zencad.zenlib.Face.transform)
FaceWrap.__wrapmethod__("fillet", FaceWrap, zencad.zenlib.Face.fillet)

Wrap = evalcache.create_class_wrap("FaceWrap", wrapclass = zencad.zenlib.Face)

def point3_hash(pnt):
	m = hashlib.sha1()
	m.update(str(pnt.x).encode("utf-8"))
	m.update(str(pnt.y).encode("utf-8"))
	m.update(str(pnt.z).encode("utf-8"))
	return m.digest()

def transform_hash(trsf):
	return "afsadfsadgasgsdfg".encode("utf-8")

evalcache.hashfuncs[zencad.zenlib.point3] = point3_hash
#evalcache.hashfuncs[zencad.zenlib.translate] = transform_hash
#evalcache.hashfuncs[zencad.zenlib.plane_mirror] = transform_hash
#evalcache.hashfuncs[zencad.zenlib.complex_transformation] = transform_hash

#FaceSweepWrap = evalcache.create_class_wrap("FaceSweepWrap", zencad.zenlib.FaceSweep, FaceWrap)

#print(zencad.zenlib.Solid.__dict__)
#zencad.zenlib.Solid.left = evalcache.FunctionHeader(Solid.left)
#zencad.zenlib.Solid.translate = evalcache.FunctionHeader(Solid.translate)

#print(zencad.zenlib.Solid.__dict__)

def solid_or_face(arr):
	if isinstance(arr[0], SolidWrap): return SolidWrap
	if isinstance(arr[0], FaceWrap): return FaceWrap
	print("???")
	exit(-1)

@evalcache.lazy(solid_or_face)
def union(arr): return zencad.zenlib.make_union(arr)

@evalcache.lazy(solid_or_face)
def difference(arr): return zencad.zenlib.make_difference(arr)

@evalcache.lazy(solid_or_face)
def intersect(arr): return zencad.zenlib.make_intersect(arr)

def points(tpls):
	return [ point3(*t) for t in tpls ]

def vectors(tpls):
	return [ zencad.zenlib.vector3(*t) for t in tpls ]

def to_vector3(v):
	try:
		if isinstance(v, zencad.zenlib.vector3):
			return v
		return zencad.zenlib.vector3(v[0], v[1], v[2])
	except Exception:
		return zencad.zenlib.vector3(0,0,v)


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
	zencad.zenlib.display_scene(scn)

#prim3d
@evalcache.lazy(SolidWrap)
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return zencad.zenlib.make_box(size[0], size[1], size[2], center)
		else:
			return zencad.zenlib.make_box(size, size, size, center)
	else:
		return zencad.zenlib.make_box(size, arg2, arg3, center)

@evalcache.lazy(SolidWrap)
def sphere(r): 
	return zencad.zenlib.make_sphere(r)

@evalcache.lazy(SolidWrap)
def cylinder(r, h, center = False): 
	return zencad.zenlib.make_cylinder(r,h,center)

@evalcache.lazy(SolidWrap)
def cone(r1, r2, h, center = False): 
	return zencad.zenlib.make_cone(r1,r2,h,center)

@evalcache.lazy(SolidWrap)
def torus(r1, r2): 
	return zencad.zenlib.make_torus(r1,r2)

#sweep
@evalcache.lazy(SolidWrap)
def linear_extrude(shp, vec, center = False):
	return zencad.zenlib.make_linear_extrude(shp, to_vector3(vec), center)

@evalcache.lazy(SolidWrap)
def pipe(prof, path):
	return zencad.zenlib.make_pipe(prof, path)

@evalcache.lazy(SolidWrap)
def pipe_shell(prof, path, frenet = False):
	return zencad.zenlib.make_pipe_shell(prof, path, frenet)

#face
@evalcache.lazy(FaceWrap)
def circle(r):
	return zencad.zenlib.make_circle(r)

@evalcache.lazy(FaceWrap)
def ngon(r, n):
	return zencad.zenlib.make_ngon(r, n)

@evalcache.lazy(FaceWrap)
def polygon(pnts):
	return zencad.zenlib.make_polygon(pnts)

@evalcache.lazy(FaceWrap)
def square(a, center = False):
	return zencad.zenlib.make_square(a, center)

@evalcache.lazy(FaceWrap)
def rectangle(a, b, center = False):
	return zencad.zenlib.make_rectangle(a, b, center)

#wire
def segment(*args, **kwargs):
	return zencad.zenlib.make_segment(*args, **kwargs)

def polysegment(*args, **kwargs):
	return zencad.zenlib.make_polysegment(*args, **kwargs)

def wcircle(*args, **kwargs):
	return zencad.zenlib.make_wcircle(*args, *kwargs)

def interpolate(*args, **kwargs):
	return zencad.zenlib.make_interpolate(*args, **kwargs)

def complex_wire(*args, **kwargs):
	return zencad.zenlib.make_complex_wire(*args, **kwargs)

@evalcache.lazy(FaceWrap)
def sweep(prof, path):
	return zencad.zenlib.make_sweep(prof, path)



def helix(*args, **kwargs):
	#return make_helix(*args, **kwargs)
	return make_long_helix(*args, **kwargs)


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
##from zencad.zenlib import ZenVertex as vertex
#
def gr(grad): return float(grad) / 180.0 * math.pi
def deg(grad): return float(grad) / 180.0 * math.pi
#from zencad.math3 import point as pnt
#
#
#
#
#from zencad.zenlib import scene
#from zencad.zenlib import camera
#from zencad.zenlib import view

def trans_type(obj, arg):
	if (isinstance(arg, SolidWrap)): return SolidWrap
	if (isinstance(arg, FaceWrap)): return FaceWrap
	print("???2")
	exit(-1)

TransformWrap = evalcache.create_class_wrap("TransformWrap", wrapclass = zencad.zenlib.transformation)
TransformWrap .__wrapmethod__("__mul__", TransformWrap, zencad.zenlib.transformation.__mul__ )
TransformWrap .__wrapmethod__("__call__", trans_type, zencad.zenlib.transformation.__call__ )

@evalcache.lazy(TransformWrap)
def translate(*args, **kwargs): return zencad.zenlib.translate(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateX(*args, **kwargs): return zencad.zenlib.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateY(*args, **kwargs): return zencad.zenlib.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def rotateZ(*args, **kwargs): return zencad.zenlib.rotateZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorXZ(*args, **kwargs): return zencad.zenlib.mirrorXZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorYZ(*args, **kwargs): return zencad.zenlib.mirrorYZ(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorXY(*args, **kwargs): return zencad.zenlib.mirrorXY(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorX(*args, **kwargs): return zencad.zenlib.mirrorX(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorY(*args, **kwargs): return zencad.zenlib.mirrorY(*args, **kwargs)

@evalcache.lazy(TransformWrap)
def mirrorZ(*args, **kwargs): return zencad.zenlib.mirrorZ(*args, **kwargs)



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