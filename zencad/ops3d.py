import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator

from zencad.util import points, vector3

@lazy.lazy(cls=shape_generator)
def linear_extrude(shp, vec, center=False):
	if isinstance(vec, (int, float)):
		vec = vector3(0,0,vec)
	return pyservoce.make_linear_extrude(shp, vector3(vec), center)

def extrude(vec): return linear_extrude(*args, **kwargs)

@lazy.lazy(cls=shape_generator)
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@lazy.lazy(cls=shape_generator)
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

@lazy.lazy(cls=shape_generator)
def sweep(shp, traj, frenet = False):
	return pyservoce.make_pipe_shell(shp, traj, frenet)

@lazy.lazy(cls=shape_generator)
def loft(arr, smooth=False):
	return pyservoce.loft(arr, smooth=smooth)

@lazy.lazy(cls=shape_generator)
def revol(shp, yaw=0.0):
	return pyservoce.revol(shp, yaw)

@lazy.lazy(cls=shape_generator)
def thicksolid(shp, t, refs):
	return pyservoce.thicksolid(shp, points(refs), t)

@lazy.lazy(cls=shape_generator)
def fillet(shp, r, refs=None): 
	if refs is None:
		return pyservoce.fillet(shp, r)
	else:
		return pyservoce.fillet(shp, r, points(refs))

@lazy.lazy(cls=shape_generator)
def chamfer(shp, r, refs=None): 
	if refs is None:
		return pyservoce.chamfer(shp, r)
	else:
		return pyservoce.chamfer(shp, r, points(refs))


pyservoce.Shape.extrude = linear_extrude
pyservoce.Shape.fillet = fillet
pyservoce.Shape.chamfer = chamfer