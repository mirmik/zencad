from zencad.zenlib import wire_segment as segment
from zencad.zenlib import wire_polysegment as polysegment
from zencad.zenlib import wire_circle_arc_by_points as arc_by_points
from zencad.zenlib import wire_circle as circle

from zencad.zenlib import wire_interpolate as interpolate

import zencad.math3

#from zencad.zenlib import wire_complex as make_wire
#import zencad.math3#

#def interpolate(pnts, tan closed = False):
	#parr = [ l[0] if isinstance(l, tuple) else l for l in lst ]
	#tarr = [ l[1] if isinstance(l, tuple) else zencad.math3.vector(0,0,0) for l in lst ]
#	return _interpolate(parr, tarr, closed)