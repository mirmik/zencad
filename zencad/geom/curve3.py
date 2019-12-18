import zencad
import pyservoce
from zencad.lazifier import lazy, nocached_shape_generator, shape_generator

from zencad.util import points, vectors

#@lazy
#def trimmed_curve2(crv, arg0, arg1):
#    return pyservoce.trimmed_curve2(crv, arg0, arg1)


#@lazy
#def ellipse(major, minor):
#    return pyservoce.curve2_ellipse(major, minor)


#@lazy
#def segment(a, b):
#    return pyservoce.curve2_segment(a, b)


@lazy
def interpolate(pnts, tangs=[], closed=False):
    return pyservoce.curve3_interpolate(points(pnts), vectors(tangs), closed)

@lazy
def extract_curve(shp):
	return pyservoce.extract_curve(shp)