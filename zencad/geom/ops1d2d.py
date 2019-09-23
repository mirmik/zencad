import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator

from zencad.util import points, vectors


@lazy.lazy(cls=shape_generator)
def fill(*args, **kwargs):
    return pyservoce.fill(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def interpolate(pnts, tangs=[], closed=False):
    return pyservoce.interpolate(points(pnts), vectors(tangs), closed)


@lazy.lazy(cls=shape_generator)
def sew(*args, **kwargs):
    return pyservoce.sew(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def fillet2d(shp, r, refs=None):
    if refs is None:
        return pyservoce.fillet2d(shp, r)
    else:
        return pyservoce.fillet2d(shp, r, points(refs))


@lazy.lazy(cls=shape_generator)
def chamfer2d(shp, r, refs=None):
    if refs is None:
        return pyservoce.chamfer2d(shp, r)
    else:
        return pyservoce.chamfer2d(shp, r, points(refs))
