import evalcache
import evalcache.dircache

import math
import hashlib

import pyservoce
from pyservoce import Scene, View, Viewer, point3, Color

__version__ = '0.6.4'

lazy = evalcache.Lazy(cache = evalcache.DirCache(".evalcache"), algo = hashlib.sha256)

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
	import zencad.shower
	zencad.shower.show(scn)

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

@lazy
def sphere(r): 
	return pyservoce.make_sphere(r)

@lazy
def cylinder(r, h, center=False, angle=None): 
	if angle is None:
		return pyservoce.make_cylinder(r,h,center)
	else:
		return pyservoce.make_cylinder(r,h,angle,center)

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

def gr(grad): 
	print("'gr' function is deprecated. Use 'deg' instead")
	return float(grad) / 180.0 * math.pi

def deg(grad): return float(grad) / 180.0 * math.pi

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

def enable_cache_diagnostic():
	evalcache.diagnostic = True
