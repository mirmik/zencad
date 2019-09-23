import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator

from zencad.util import points, vector3


@lazy.lazy(cls=shape_generator)
def linear_extrude(proto, vec, center=False):
    if isinstance(vec, (int, float)):
        vec = vector3(0, 0, vec)
    return pyservoce.linear_extrude(proto, vector3(vec), center)


def extrude(vec):
    return linear_extrude(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def pipe(proto, path):
    return pyservoce.pipe(proto, path)


@lazy.lazy(cls=shape_generator)
def pipe_shell(proto, path, frenet=False):
    return pyservoce.pipe_shell(proto, path, frenet)


@lazy.lazy(cls=shape_generator)
def sweep(proto, path, frenet=False):
    return pyservoce.pipe_shell(proto, path, frenet)


@lazy.lazy(cls=shape_generator)
def loft(arr, smooth=False):
    return pyservoce.loft(arr, smooth=smooth)


@lazy.lazy(cls=shape_generator)
def revol(proto, yaw=0.0):
    return pyservoce.revol(proto, yaw)


@lazy.lazy(cls=shape_generator)
def thicksolid(proto, t, refs):
    return pyservoce.thicksolid(proto, points(refs), t)


@lazy.lazy(cls=shape_generator)
def fillet(proto, r, refs=None):
    if refs is None:
        return pyservoce.fillet(proto, r)
    else:
        return pyservoce.fillet(proto, r, points(refs))


@lazy.lazy(cls=shape_generator)
def chamfer(proto, r, refs=None):
    if refs is None:
        return pyservoce.chamfer(proto, r)
    else:
        return pyservoce.chamfer(proto, r, points(refs))


pyservoce.Shape.extrude = linear_extrude
pyservoce.Shape.fillet = fillet
pyservoce.Shape.chamfer = chamfer
