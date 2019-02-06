import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import angle_pair


@lazy.lazy(cls=nocached_shape_generator)
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return pyservoce.box(size[0], size[1], size[2], center)
		else:
			return pyservoce.box(size, size, size, center)
	else:
		return pyservoce.box(size, arg2, arg3, center)


def cube(*args, **kwargs): return box(*args, **kwargs)


@lazy.lazy(cls=nocached_shape_generator)
def sphere(r): 
	return pyservoce.sphere(r)


@lazy.lazy(cls=nocached_shape_generator)
def cylinder(r, h, center=False, angle=None): 
	if angle is None:
		return pyservoce.cylinder(r,h,center)
	else:
		ap = angle_pair(angle)
		return pyservoce.cylinder(r, h, ap[0], ap[1], center)


@lazy.lazy(cls=nocached_shape_generator)
def cone(r1, r2, h, center = False, angle=None): 
	if angle is None:
		return pyservoce.cone(r1,r2,h,center)
	else:
		ap = angle_pair(angle)
		return pyservoce.cone(r1,r2,h,ap[0],ap[1],center)


@lazy.lazy(cls=nocached_shape_generator)
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


@lazy.lazy(cls=nocached_shape_generator)
def halfspace(): 
	return pyservoce.halfspace()