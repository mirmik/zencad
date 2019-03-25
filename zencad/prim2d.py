import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import angle_pair, points


@lazy.lazy(cls=nocached_shape_generator)
def rectangle(a, b=None, center = False, wire=False):
	if b is None:
		return pyservoce.square(a, center, wire)
	return pyservoce.rectangle(a, b, center, wire)


@lazy.lazy(cls=nocached_shape_generator)
def square(a, center = False, wire=False):
	return pyservoce.square(a, center, wire)


@lazy.lazy(cls=nocached_shape_generator)
def circle(r, angle=None, wire=False):
	if angle is not None:
		ap = angle_pair(angle)

	return pyservoce.circle(r, angle, wire=wire)


@lazy.lazy(cls=nocached_shape_generator)
def ellipse(r1, r2, angle=None, wire=False):
	if angle is not None:
		ap = angle_pair(angle)

	return pyservoce.ellipse(r1, r2, angle, wire=wire)


@lazy.lazy(cls=nocached_shape_generator)
def ngon(r, n, wire=False):
	return pyservoce.ngon(r, n, wire)


@lazy.lazy(cls=nocached_shape_generator)
def polygon(pnts, wire=False):
	if wire:
		return pyservoce.polysegment(points(pnts), True)
	else:
		return pyservoce.polygon(points(pnts))


@lazy.lazy(cls=shape_generator)
def textshape(*args, **kwargs):
	return pyservoce.textshape(*args, **kwargs)
