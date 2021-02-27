from zencad.lazifier import *
from zencad.shape import Shape, nocached_shape_generator, shape_generator


def _restore_shapetype(shp):
    if len(shp.solids()) == 1:
        return shp.solids()[0]

    if len(shp.shells()) == 1:
        return shp.shells()[0]

    elif len(shp.faces()) == 1:
        return shp.faces()[0]

    elif len(shp.wires()) == 1:
        return shp.wires()[0]

    elif len(shp.edges()) == 1:
        return shp.edges()[0]

    else:
        raise Exception("type is not supported: {}".format(shp.shapetype()))


@lazy.lazy(cls=shape_generator)
def restore_shapetype(shp):
    return _restore_shapetype(shp)
