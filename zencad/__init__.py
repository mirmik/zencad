import math

import pyservoce
from pyservoce import point3, vector3
from pyservoce import Scene, View, Viewer, Color

from zencad.visual import screen
from zencad.transform import *

from zencad.lazy import lazy
import evalcache

__version__ = '0.8.1'

#def point3(*t):
#	return pyservoce.point3(*t)

#def vector3(*t):
#	return vector3(*t)

def points(tpls):
	return [ point3(*t) for t in tpls ]

def vectors(tpls):
	return [ vector3(*t) for t in tpls ]

#def to_vector3(v):
#	try:
#		if isinstance(v, pyservoce.vector3):
#			return v
#		return pyservoce.vector3(v[0], v[1], v[2])
#	except Exception:
#		return pyservoce.vector3(0,0,v)

##display
default_scene = Scene()

def display(shp):
	if isinstance(shp, evalcache.LazyObject):
		default_scene.add(evalcache.unlazy(shp))
	else:
		default_scene.add(shp)

def show(scn = default_scene):
	import zencad.shower
	#print("show")
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
def linear_extrude(*args, **kwargs):
	return pyservoce.make_linear_extrude(*args, **kwargs)

@lazy
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@lazy
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

#face
@lazy
def circle(*args, **kwargs):
	return pyservoce.make_circle(*args, **kwargs)

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
def segment(pnt0, pnt1):
	return pyservoce.make_segment(pyservoce.point3(pnt0), pyservoce.point3(pnt1))

@lazy
def polysegment(lst, closed = False):
	lst = [pyservoce.point3(p) for p in lst]
	return pyservoce.make_polysegment(lst, closed)

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

def enable_cache_diagnostic():
	evalcache.diagnostic = True

def to_stl(model, path, delta):
	pyservoce.make_stl(path, model.unlazy(), delta)