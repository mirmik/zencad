import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import angle_pair, deg, points

@lazy.lazy(cls=nocached_shape_generator)
def nullshape():
    return pyservoce.box(1,1,1) - pyservoce.box(1,1,1)

@lazy.lazy(cls=nocached_shape_generator)
def box(size, arg2=None, arg3=None, center=False, shell=False):
    if arg3 == None:
        if hasattr(size, "__getitem__"):
            m = pyservoce.box(size[0], size[1], size[2], center)
        else:
            m = pyservoce.box(size, size, size, center)
    else:
        m = pyservoce.box(size, arg2, arg3, center)

    if shell:
        return m.shells()[0]
    else:
        return m


def cube(*args, **kwargs):
    return box(*args, **kwargs)


@lazy.lazy(cls=nocached_shape_generator)
def sphere(r, yaw=None, pitch=None, shell=False):
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
            m = pyservoce.sphere(r=r, pitch0=pitch[0], pitch1=pitch[1], yaw=yaw)
        else:
            m = pyservoce.sphere(r=r, yaw=yaw)

    else:
        if pitch is not None:
            m = pyservoce.sphere(r=r, pitch0=pitch[0], pitch1=pitch[1])
        else:
            m = pyservoce.sphere(r=r)

    if shell:
        return m.shells()[0]
    else:
        return m


@lazy.lazy(cls=nocached_shape_generator)
def cylinder(r, h, center=False, yaw=None, shell=False):
    if yaw is None:
        m = pyservoce.cylinder(r=r, h=h, center=center)
    else:
        m = pyservoce.cylinder(r=r, h=h, yaw=yaw, center=center)

    if shell:
        return m.shells()[0]
    else:
        return m


@lazy.lazy(cls=nocached_shape_generator)
def cone(r1, r2, h, center=False, yaw=None, shell=False):
    if yaw is None:
        m = pyservoce.cone(r1=r1, r2=r2, h=h, center=center)
    else:
        m = pyservoce.cone(r1=r1, r2=r2, h=h, yaw=yaw, center=center)

    if shell:
        return m.shells()[0]
    else:
        return m


@lazy.lazy(cls=nocached_shape_generator)
def torus(r1, r2, yaw=None, pitch=None, shell=False):
    if pitch is not None:
        pitch = angle_pair(pitch)
        if yaw is not None:
            m = pyservoce.torus(
                r1=r1, r2=r2, pitch0=pitch[0], pitch1=pitch[1], yaw=yaw
            )
        else:
            m = pyservoce.torus(r1=r1, r2=r2, pitch0=pitch[0], pitch1=pitch[1])
    else:
        if yaw is not None:
            m = pyservoce.torus(r1=r1, r2=r2, yaw=yaw)
        else:
            #return pyservoce.torus(r1=r1, r2=r2)
            m = (pyservoce.torus(r1=r1, r2=r2, yaw=deg(180)) 
                + pyservoce.torus(r1=r1, r2=r2, yaw=deg(180)).rotateZ(deg(180)))

    if shell:
        return m.shells()[0]
    else:
        return m

@lazy.lazy(cls=nocached_shape_generator)
def halfspace():
    return pyservoce.halfspace()


@lazy.lazy(cls=nocached_shape_generator)
def polyhedron(pnts, faces, shell=False):
    pnts = points(pnts)
    shl = pyservoce.polyhedron_shell(pnts, faces)

    if shell:
        return shl
    else:
        return shl.fill()    

@lazy.lazy(cls=nocached_shape_generator)
def make_solid(*args, **kwargs):
    return pyservoce.make_solid(*args, **kwargs)

@lazy.lazy
def convex_hull(pnts, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental=False, qhull_options=None).simplices

    return faces

@lazy.lazy(cls=shape_generator)
def convex_hull_shape(pnts, shell=False, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental, qhull_options).simplices
    m = polyhedron(pnts, faces, shell=shell)

    return m