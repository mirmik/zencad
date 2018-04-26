import math
from zencad.zenlib import *

def union(arr): return make_union(arr)
def difference(arr): return make_difference(arr)
def intersect(arr): return make_intersect(arr)

def points(tpls):
	return [ point3(*t) for t in tpls ]

def vectors(tpls):
	return [ vector3(*t) for t in tpls ]

def to_vector3(v):
	if isinstance(v, vector3):
		return v
	return vector3(v[0], v[1], v[2])

def enable_cache(arg):
	print("Warn: cache in rework state. comming soon.")

#display
default_scene = Scene()

def display(shp):
	default_scene.add(shp)

def show():
	display_scene(default_scene)

#prim3d
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return make_box(size[0], size[1], size[2], center)
		else:
			return make_box(size, size, size, center)
	else:
		return make_box(size, arg2, arg3, center)

def sphere(r): 
	return make_sphere(r)

def cylinder(r, h, center = False): 
	return make_cylinder(r,h,center)

def cone(r1, r2, h, center = False): 
	return make_cone(r1,r2,h,center)

def torus(r1, r2): 
	return make_torus(r1,r2)

#sweep
def linear_extrude(shp, vec):
	return make_linear_extrude(shp, to_vector3(vec))

def pipe(prof, path):
	return make_pipe(prof, path)

#face
def circle(r):
	return make_circle(r)

def ngon(r, n):
	return make_ngon(r, n)

def polygon(pnts):
	return make_polygon(pnts)

def square(a, center = False):
	return make_square(a, center)

def rectangle(a, b, center = False):
	return make_rectangle(a, b, center)

#wire
def segment(*args, **kwargs):
	return make_segment(*args, **kwargs)

def interpolate(*args, **kwargs):
	return make_interpolate(*args, **kwargs)

def complex_wire(*args, **kwargs):
	return make_complex_wire(*args, **kwargs)

def sweep(prof, path):
	return make_sweep(prof, path)


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
def gr(rad): return rad / 180 * math.pi
#from zencad.math3 import point as pnt
#
#
#def execfile(path):
#	with open(path) as f:
#		code = compile(f.read(), path, 'exec')
#		exec(code, globals(), locals())
#		return locals()
#
#
#from zencad.zenlib import scene
#from zencad.zenlib import camera
#from zencad.zenlib import view