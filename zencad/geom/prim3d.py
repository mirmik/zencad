import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import angle_pair, deg

@lazy.lazy(cls=nocached_shape_generator)
def nullshape():
    return pyservoce.box(1,1,1) - pyservoce.box(1,1,1)

@lazy.lazy(cls=nocached_shape_generator)
def box(size, arg2=None, arg3=None, center=False):
    if arg3 == None:
        if hasattr(size, "__getitem__"):
            return pyservoce.box(size[0], size[1], size[2], center)
        else:
            return pyservoce.box(size, size, size, center)
    else:
        return pyservoce.box(size, arg2, arg3, center)


def cube(*args, **kwargs):
    return box(*args, **kwargs)


@lazy.lazy(cls=nocached_shape_generator)
def sphere(r, yaw=None, pitch=None):
    if yaw is not None:
        if yaw > deg(360):
            raise Exception("Wrong parametr `yaw`. yaw defined in [0, 2*pi]")

    if pitch is not None:
        pitch = angle_pair(pitch)

        if pitch[0] > pitch[1]:
            raise Exception(
                "Wrong parametr `pitch`. pitch[0] should be less then pitch[1]"
            )

        if pitch[0] > pitch[1]:
            raise Exception(
                "Wrong parametr `pitch`. pitch[0] should be less then pitch[1]"
            )

        if (
            pitch[0] > deg(90)
            or pitch[1] > deg(90)
            or pitch[0] < -deg(90)
            or pitch[1] < -deg(90)
        ):
            raise Exception(
                "Wrong parametr `pitch`. pitch[0] and pitch[1] defined in [-pi/2, pi/2]"
            )

    if yaw is not None:
        if pitch is not None:
            return pyservoce.sphere(r=r, pitch0=pitch[0], pitch1=pitch[1], yaw=yaw)
        else:
            return pyservoce.sphere(r=r, yaw=yaw)

    else:
        if pitch is not None:
            return pyservoce.sphere(r=r, pitch0=pitch[0], pitch1=pitch[1])
        else:
            return pyservoce.sphere(r=r)


@lazy.lazy(cls=nocached_shape_generator)
def cylinder(r, h, center=False, yaw=None):
    if yaw is None:
        return pyservoce.cylinder(r=r, h=h, center=center)
    else:
        return pyservoce.cylinder(r=r, h=h, yaw=yaw, center=center)


@lazy.lazy(cls=nocached_shape_generator)
def cone(r1, r2, h, center=False, yaw=None):
    if yaw is None:
        return pyservoce.cone(r1=r1, r2=r2, h=h, center=center)
    else:
        return pyservoce.cone(r1=r1, r2=r2, h=h, yaw=yaw, center=center)


@lazy.lazy(cls=nocached_shape_generator)
def torus(r1, r2, yaw=None, pitch=None):
    if pitch is not None:
        pitch = angle_pair(pitch)
        if yaw is not None:
            return pyservoce.torus(
                r1=r1, r2=r2, pitch0=pitch[0], pitch1=pitch[1], yaw=yaw
            )
        else:
            return pyservoce.torus(r1=r1, r2=r2, pitch0=pitch[0], pitch1=pitch[1])
    else:
        if yaw is not None:
            return pyservoce.torus(r1=r1, r2=r2, yaw=yaw)
        else:
            #return pyservoce.torus(r1=r1, r2=r2)
            return (pyservoce.torus(r1=r1, r2=r2, yaw=deg(180)) 
                + pyservoce.torus(r1=r1, r2=r2, yaw=deg(180)).rotateZ(deg(180)))


@lazy.lazy(cls=nocached_shape_generator)
def halfspace():
    return pyservoce.halfspace()
