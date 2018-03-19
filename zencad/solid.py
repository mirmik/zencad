from zencad.zenlib import solid_box as box
from zencad.zenlib import solid_sphere as sphere
from zencad.zenlib import solid_cylinder as cylinder
from zencad.zenlib import solid_torus as torus
from zencad.zenlib import solid_wedge as wedge
from zencad.zenlib import solid_load as load
from zencad.zenlib import solid_loft as loft

from zencad.zenlib import solid_linear_extrude as __linear_extrude

import zencad.math3

def linear_extrude(face, vector):
	return __linear_extrude(face, zencad.math3.vector(*vector))