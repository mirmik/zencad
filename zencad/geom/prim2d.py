import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import angle_pair, points


@lazy.lazy(cls=nocached_shape_generator)
def rectangle(a, b=None, center=False, wire=False):
    if b is None:
        b=a
    
    if wire:
        foo = pyservoce.rectangle_wire
    else:
        foo = pyservoce.rectangle

    return foo(a, b, center)


@lazy.lazy(cls=nocached_shape_generator)
def square(a, center=False, wire=False):
    if wire:
        foo = pyservoce.square_wire
    else:
        foo = pyservoce.square

    return foo(a, center)


@lazy.lazy(cls=nocached_shape_generator)
def circle(r, angle=None, wire=False):
    if wire:
        foo = pyservoce.circle_edge
    else:
        foo = pyservoce.circle

    if angle is not None:
        angle = angle_pair(angle)
        return foo(r, angle[0], angle[1])
    else:
        return foo(r)


@lazy.lazy(cls=nocached_shape_generator)
def ellipse(r1, r2, angle=None, wire=False):
    if wire:
        foo = pyservoce.ellipse_edge
    else:
        foo = pyservoce.ellipse

    if r1 < r2:
        raise ValueError("In ellipse r1 must be greater then r2")

    if angle is not None:
        angle = angle_pair(angle)
        return foo(r1, r2, angle[0], angle[1])
    else:
        return foo(r1, r2)


@lazy.lazy(cls=nocached_shape_generator)
def ngon(r, n, wire=False):
    if wire:
        foo = pyservoce.ngon_wire
    else:
        foo = pyservoce.ngon

    return foo(r, n)


@lazy.lazy(cls=nocached_shape_generator)
def polygon(pnts, wire=False):
    if wire:
        return pyservoce.polysegment(points(pnts), True)
    else:
        return pyservoce.polygon(points(pnts))


@lazy.lazy(cls=shape_generator)
def textshape(text, fontpath, size, center=False):
    m = pyservoce.textshape(text, fontpath, size)
    if center:
        (x,y,z) = m.center()
        m = m.translate(-x, -y, -z)
    return m 

@lazy.lazy(cls=shape_generator)
def infplane(*args, **kwargs):
    return pyservoce.infplane(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def ruled(a, b):
    if a.shapetype()=="edge" and b.shapetype()=="edge":
        return pyservoce.ruled_face(a, b)

    else:
        return pyservoce.ruled_shell(a, b)

    #return pyservoce.infplane(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def trivial_tube(spine, r):
    return pyservoce.trivial_tube(spine, r)
    
@lazy.lazy(cls=shape_generator)
def tube(spine, r, tol=1e-6, cont=2, maxdegree=3, maxsegm=20, bounds=False):
    ret, f, l = pyservoce.tube(spine, r, tol, cont, maxdegree, maxsegm)
    
    if bounds:
        return (ret,f,l)

    return ret


#@lazy.lazy(cls=shape_generator)
#def tube_by_points(pnts, r1, r2, tol=1e-6, cont=2, maxdegree=3, maxsegm=20):
 #   wire = tube_wire_by_points(pnts, r2)
  #  return pyservoce.tube(wire, r1, cont, maxdegree, maxsegm)


@lazy.lazy(cls=shape_generator)
def make_face(*args, **kwargs):
    return pyservoce.make_face(*args, **kwargs)