import zencad
import pyservoce

from zencad.lazifier import lazy, nocached_shape_generator, shape_generator


@lazy.lazy(cls=nocached_shape_generator)
def cylinder(r):
    return pyservoce.surface_cylinder(r)
