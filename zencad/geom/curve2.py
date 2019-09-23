import zencad
import pyservoce
from zencad.lazifier import lazy, nocached_shape_generator, shape_generator


@lazy
def trimmed_curve2(crv, arg0, arg1):
    return pyservoce.trimmed_curve2(crv, arg0, arg1)


@lazy
def ellipse(major, minor):
    return pyservoce.curve2_ellipse(major, minor)


@lazy
def segment(a, b):
    return pyservoce.curve2_segment(a, b)
