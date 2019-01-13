import zencad
import pyservoce

from zencad.lazifier import lazy, nocached_shape_generator, shape_generator

from pyservoce import trimmed_curve2

@lazy.lazy(cls=nocached_shape_generator)
def ellipse(major, minor):
	return pyservoce.ellipse(major, minor)