import math

import pyservoce
from pyservoce import point3, vector3
from pyservoce import Scene, View, Viewer, Color

from zencad.visual import screen
from zencad.transform import *

from zencad.lazy import lazy 
from zencad.lazy import lazyfile
from zencad.lazy import disable_cache, test_mode
import evalcache

from zencad.util import deg, angle_pair, points, vectors

__version__ = '0.11.1'

##display
default_scene = Scene()

def display(shp):
	if isinstance(shp, evalcache.LazyObject):
		default_scene.add(evalcache.unlazy(shp))
	else:
		default_scene.add(shp)

def show(scene=default_scene, *args, **kwargs):
	import zencad.shower
	zencad.shower.show(scene, *args, **kwargs)

##prim3d
@lazy
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return pyservoce.box(size[0], size[1], size[2], center)
		else:
			return pyservoce.box(size, size, size, center)
	else:
		return pyservoce.box(size, arg2, arg3, center)

@lazy
def sphere(r): 
	return pyservoce.sphere(r)

@lazy
def cylinder(r, h, center=False, angle=None): 
	if angle is None:
		return pyservoce.cylinder(r,h,center)
	else:
		ap = angle_pair(angle)
		return pyservoce.cylinder(r, h, ap[0], ap[1], center)

@lazy
def cone(r1, r2, h, center = False, angle=None): 
	if angle is None:
		return pyservoce.cone(r1,r2,h,center)
	else:
		ap = angle_pair(angle)
		return pyservoce.cone(r1,r2,h,ap[0],ap[1],center)

@lazy
def torus(r1, r2, uangle=None, vangle=None): 
	if vangle is not None:
		vangle = angle_pair(vangle)

	if uangle is not None and vangle is not None:
		return pyservoce.torus(r1,r2,vangle[0],vangle[1],uangle)

	if uangle is not None:
		return pyservoce.torus(r1,r2,uangle)

	if vangle is not None:
		return pyservoce.torus(r1,r2,vangle[0],vangle[1])

	return pyservoce.torus(r1,r2)

@lazy
def halfspace(): 
	return pyservoce.halfspace()

@lazy
def linear_extrude(*args, **kwargs):
	return pyservoce.make_linear_extrude(*args, **kwargs)

@lazy
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@lazy
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

@lazy
def loft(arr):
	return pyservoce.loft(arr)

#face
@lazy
def circle(r, angle=None, wire=False):
	if angle is not None:
		ap = angle_pair(angle)

	if angle is not None:
		return pyservoce.circle(r, ap[0], ap[1], wire=wire)
	else:
		return pyservoce.circle(r, wire=wire)

@lazy
def ellipse(r1, r2, angle=None, wire=False):
	if angle is not None:
		ap = angle_pair(angle)

	if angle is not None:
		return pyservoce.ellipse(r1, r2, ap[0], ap[1], wire=wire)
	else:
		return pyservoce.ellipse(r1, r2, wire=wire)

@lazy
def ngon(r, n, wire=False):
	return pyservoce.ngon(r, n, wire)

@lazy
def polygon(pnts):
	return pyservoce.polygon(points(pnts))

@lazy
def square(a, center = False, wire=False):
	return pyservoce.square(a, center, wire)

@lazy
def rectangle(a, b, center = False, wire=False):
	return pyservoce.rectangle(a, b, center, wire)

@lazy
def textshape(*args, **kwargs):
	return pyservoce.textshape(*args, **kwargs)

#wire
@lazy
def segment(pnt0, pnt1):
	return pyservoce.segment(pyservoce.point3(pnt0), pyservoce.point3(pnt1))

@lazy
def polysegment(lst, closed = False):
	return pyservoce.polysegment(points(lst), closed)

@lazy
def wcircle(*args, **kwargs):
	print("def wcircle(*args, **kwargs): deprecated")
	return pyservoce.make_wcircle(*args, *kwargs)

@lazy
def interpolate(pnts, tangs=[], closed=False):
	return pyservoce.interpolate(points(pnts), vectors(tangs), closed)

@lazy
def complex_wire(*args, **kwargs):
	return pyservoce.complex_wire(*args, **kwargs)

@lazy
def sweep(prof, path):
	print("def sweep(prof, path): deprecated")
	return pyservoce.make_sweep(prof, path)

@lazy
def helix(*args, **kwargs):
	#return make_helix(*args, **kwargs)
	return pyservoce.long_helix(*args, **kwargs)

def gr(grad): 
	print("'gr' function is deprecated. Use 'deg' instead")
	return float(grad) / 180.0 * math.pi

def enable_cache_diagnostic():
	evalcache.diagnostic = True

#CONVERT
@lazyfile("path")
def to_stl(model, path, delta):
	pyservoce.make_stl(model, path, delta)

@lazyfile("path")
def brep_write(model, path):
	pyservoce.brep_write(model, path)