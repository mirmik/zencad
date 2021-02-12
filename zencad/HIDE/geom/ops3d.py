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


def extrude(*args, **kwargs):
	return linear_extrude(*args, **kwargs)

@lazy.lazy(cls=shape_generator)
def pipe_0(proto, spine):
	return pyservoce.pipe_0(proto, spine)

@lazy.lazy(cls=shape_generator)
def pipe(profile, spine, frenet=False, mode="corrected_frenet", force_approx_c1=False, path=None, proto=None):
	if path is not None:
		spine = path
		print("pipe: path option was renamed. use spine instead")

	if proto is not None:
		profile = proto
		print("pipe: proto option was renamed. use profile instead")

	if frenet is True:
		mode = "frenet"

	if isinstance(profile, pyservoce.Solid):
		if len(profile.shells()) != 1:
			raise Exception("pipe: Solids with more then one shells are not supported")
		else:
			profile = profile.shells()[0]

	return pyservoce.pipe(profile, spine, mode, force_approx_c1)


@lazy.lazy(cls=shape_generator)
def pipe_shell(
		profiles, 
		spine, 
		frenet=False, 
		binormal=vector3(0,0,0), 
		parallel=vector3(0,0,0), 
		force_approx_c1=False, 
		solid=True,
		discrete=False,
		transition=0, 
		path=None,
		proto=None):
	if path is not None:
		spine = path
		print("pipe: path option is renamed. use spine instead")
	if proto is not None:
		profiles = [proto]
		print("pipe: proto option was renamed. use profile instead")

	fwires=[]
	for w in profiles:
		if w.shapetype() == "edge":
			fwires.append(w.as_edge())
			
		elif w.shapetype() == "face":
			if (len(w.wires())==1):
				fwires.append(w.wires()[0])
			else:
				raise Exception("faces with more than one wire is unsupported")

		else:
			fwires.append(w)

	return pyservoce.pipe_shell(
		profiles=fwires, 
		spine=spine, 
		frenet=frenet, 
		force_approx_c1=force_approx_c1, 
		binormal=vector3(binormal),
		parallel=vector3(parallel),
		discrete=discrete,
		transition=transition,
		solid=solid)

@lazy.lazy(cls=shape_generator)
def sweep(proto, path, frenet=False):
	print("sweep operation is deprecated. use pipe_shell instead")
	return pyservoce.pipe_shell([proto], path, frenet)


@lazy.lazy(cls=shape_generator)
def loft(arr, smooth=False, shell=False, maxdegree=4):
	return pyservoce.loft(arr, smooth=smooth, solid=not shell, maxdegree=maxdegree)

@lazy.lazy(cls=shape_generator)
def revol(profile, r=None, yaw=0.0):
	if r is not None:
		profile = profile.rotX(deg(90)).movX(r)

	return pyservoce.revol(profile, yaw)

@lazy.lazy(cls=shape_generator)
def revol2(profile, r, n=30, yaw=(0,deg(360)), roll=(0,0), sects=False, nparts=None):
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

		for w in profile.wires():
			m=zencad.geom.transform.rotate_array2(
				r=r,
				n=part_n,
				yaw=part_yaw,
				roll=part_roll,
				endpoint=endpoint,
				array=True)(w)
	
			arrs.append(m)
	
		# Радиус окружности не имеет значения.
			rets.append(
				pyservoce.pipe_shell(
					profiles=m, 
					spine=zencad.geom.prim2d.circle(
						r=100,angle=part_yaw,wire=True).unlazy(), 
					#force_approx_c1=True, 
					frenet=True))
	
		if sects:
			return arrs

	return zencad.geom.boolean.union(rets)


@lazy.lazy(cls=shape_generator)
def thicksolid(proto, t, refs):
	return pyservoce.thicksolid(proto, points(refs), t)

@lazy.lazy(cls=shape_generator)
def offset(proto, r):
	return pyservoce.offset_shape(proto, r)


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




@lazy.lazy(cls=shape_generator)
def project(*args, **kwargs):
	return pyservoce.project(*args, **kwargs)