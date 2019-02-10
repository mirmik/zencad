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

	if angle is not None:
		return pyservoce.circle(r, ap[0], ap[1], wire=wire)
	else:
		return pyservoce.circle(r, wire=wire)


@lazy.lazy(cls=nocached_shape_generator)
def ellipse(r1, r2, angle=None, wire=False):
	if angle is not None:
		ap = angle_pair(angle)

	if angle is not None:
		return pyservoce.ellipse(r1, r2, ap[0], ap[1], wire=wire)
	else:
		return pyservoce.ellipse(r1, r2, wire=wire)


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
