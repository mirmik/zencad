from zencad.zenlib import solid_box as _box

from zencad.zenlib import solid_cylinder as cylinder
from zencad.zenlib import solid_cone as cone
from zencad.zenlib import solid_sphere as sphere
from zencad.zenlib import solid_torus as torus

#from zencad.zenlib import solid_wedge as wedge
#from zencad.zenlib import solid_load as load
#from zencad.zenlib import solid_loft as loft
#from zencad.zenlib import solid_pipe as pipe
#
#from zencad.zenlib import solid_linear_extrude as __linear_extrude
#
#import zencad.math3

def linear_extrude(face, vector):
	return __linear_extrude(face, zencad.math3.vector(*vector))

def box(size, arg2 = None, arg3 = None, center = False):
	if arg3 == None:
		if hasattr(size, '__getitem__'):
			return _box(size[0], size[1], size[2], center)
		else:
			return _box(size, size, size, center)
	else:
		return _box(size, arg2, arg3, center)