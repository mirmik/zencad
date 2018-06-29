import evalcache

import math
from zencad.zenlib import *

@evalcache.lazy
def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return make_box(size[0], size[1], size[2], center)
		else:
			return make_box(size, size, size, center)
	else:
		return make_box(size, arg2, arg3, center)

@evalcache.lazy
def sphere(r): 
	return make_sphere(r)

@evalcache.lazy
def cylinder(r, h, center = False): 
	return make_cylinder(r,h,center)

@evalcache.lazy
def cone(r1, r2, h, center = False): 
	return make_cone(r1,r2,h,center)

@evalcache.lazy
def torus(r1, r2): 
	return make_torus(r1,r2)
