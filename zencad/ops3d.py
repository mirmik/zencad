import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator

@lazy.lazy(cls=shape_generator)
def linear_extrude(*args, **kwargs):
	return pyservoce.make_linear_extrude(*args, **kwargs)

@lazy.lazy(cls=shape_generator)
def pipe(prof, path):
	return pyservoce.make_pipe(prof, path)

@lazy.lazy(cls=shape_generator)
def pipe_shell(prof, path, frenet = False):
	return pyservoce.make_pipe_shell(prof, path, frenet)

@lazy.lazy(cls=shape_generator)
def loft(arr):
	return pyservoce.loft(arr)

@lazy.lazy(cls=shape_generator)
def revol(shp, angle=0.0):
	return pyservoce.revol(shp, angle)

@lazy.lazy(cls=shape_generator)
def thicksolid(shp, pnts, t):
	return pyservoce.thicksolid(shp, points(pnts), t)

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


pyservoce.Shape.fillet = fillet
pyservoce.Shape.chamfer = chamfer