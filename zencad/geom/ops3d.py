import pyservoce

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import points, vector3
from zencad.util import deg

import zencad.geom

@lazy.lazy(cls=shape_generator)
def linear_extrude(proto, vec, center=False):
	if isinstance(vec, (int, float)):
		vec = vector3(0, 0, vec)
	return pyservoce.linear_extrude(proto, vector3(vec), center)


def extrude(vec):
	return linear_extrude(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def pipe(proto, path):
	return pyservoce.pipe(proto, path)


@lazy.lazy(cls=shape_generator)
def pipe_shell(proto, path, frenet=False, approx_c1=False):
	if isinstance(proto, pyservoce.libservoce.Shape):
		return pyservoce.pipe_shell(proto, path, frenet)

	return pyservoce.pipe_shell(proto, path, frenet, approx_c1)

@lazy.lazy(cls=shape_generator)
def pipe_shell2(proto, path, auxspine, car):
	return pyservoce.pipe_shell(proto, path, auxspine, car)


@lazy.lazy(cls=shape_generator)
def sweep(proto, path, frenet=False):
	return pyservoce.pipe_shell(proto, path, frenet)


@lazy.lazy(cls=shape_generator)
def loft(arr, smooth=False):
	return pyservoce.loft(arr, smooth=smooth)

@lazy.lazy(cls=shape_generator)
def revol(proto, r=None, yaw=0.0):
	if r is not None:
		proto = proto.rotX(deg(90)).movX(r)

	return pyservoce.revol(proto, yaw)

@lazy.lazy(cls=shape_generator)
def revol2(proto, r, n=30, yaw=(0,deg(360)), roll=(0,0), sects=False, nparts=None):
	rets=[]
	arrs=[]

	is_full_circle = abs((yaw[1]-yaw[0]) - deg(360)) < 0.000001

	if is_full_circle:
		endpoint = False
		if nparts == None:
			nparts = 2 

	else:
		endpoint = True
		if nparts == None:
			nparts = 1 

	yaw_dist = yaw[1] - yaw[0]
	roll_dist = roll[1] - roll[0]
	yaw_step = yaw_dist / nparts
	roll_step = roll_dist / nparts

	def part_of_interval(part, total, a, b):
		total_p = total + 1
		
		koeff = lambda idx, tot: idx / tot
		point = lambda a, b, k: a*(1-k) + b*k

		return(point(a,b,koeff(part,total)), point(a,b,koeff(part+1,total)))

	for ipart in range(nparts):
		part_n = n // nparts
		part_yaw = part_of_interval(ipart, nparts, yaw[0], yaw[1])
		part_roll = part_of_interval(ipart, nparts, roll[0], roll[1])

		for w in proto.wires():
			m=zencad.geom.transform.rotate_array2(
				r=r,
				n=part_n,
				yaw=part_yaw,
				roll=part_roll,
				endpoint=endpoint)(w)
	
			arrs.append(m)
	
		# Радиус окружности не имеет значения.
			rets.append(
				pyservoce.pipe_shell(
					prof=m, 
					path=zencad.geom.prim2d.circle(
						r=100,angle=part_yaw,wire=True).unlazy(), 
					approx_c1=True, 
					isFrenet=True))
	
		if sects:
			return arrs

	return zencad.geom.boolean.union(rets)


@lazy.lazy(cls=shape_generator)
def thicksolid(proto, t, refs):
	return pyservoce.thicksolid(proto, points(refs), t)


@lazy.lazy(cls=shape_generator)
def fillet(proto, r, refs=None):
	if refs is None:
		return pyservoce.fillet(proto, r)
	else:
		return pyservoce.fillet(proto, r, points(refs))


@lazy.lazy(cls=shape_generator)
def chamfer(proto, r, refs=None):
	if refs is None:
		return pyservoce.chamfer(proto, r)
	else:
		return pyservoce.chamfer(proto, r, points(refs))


pyservoce.Shape.extrude = linear_extrude
pyservoce.Shape.fillet = fillet
pyservoce.Shape.chamfer = chamfer
