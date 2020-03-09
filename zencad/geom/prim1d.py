import pyservoce
from zencad.lazifier import lazy, shape_generator, nocached_shape_generator

from zencad.util import points, point3


@lazy.lazy(cls=nocached_shape_generator)
def segment(pnt0, pnt1):
	return pyservoce.segment(pyservoce.point3(pnt0), pyservoce.point3(pnt1))


@lazy.lazy(cls=shape_generator)
def polysegment(lst, closed=False):
	return pyservoce.polysegment(points(lst), closed)


@lazy.lazy(cls=nocached_shape_generator)
def circle_arc(p1, p2, p3):
	"""Построение дуги круга по трем точкам"""
	return pyservoce.circle_arc(point3(p1), point3(p2), point3(p3))


@lazy.lazy(cls=shape_generator)
def helix(r, h, step, angle=0, left=False):
	# return make_helix(*args, **kwargs)
	return pyservoce.long_helix(
		radius=r, height=h, step=step, angle=angle, leftHanded=left
	)

@lazy.lazy(cls=nocached_shape_generator)
def bezier(pnts, weights=None):
	"""Построение дуги круга по трем точкам"""
	pnts = points(pnts)

	if weights:
		return pyservoce.bezier(pnts, weights)
	else:
		return pyservoce.bezier(pnts)

@lazy.lazy(cls=nocached_shape_generator)
def bspline(pnts, knots, muls, degree, periodic=False, check_rational=True, weights=None):
	"""Построение дуги круга по трем точкам"""
	pnts = points(pnts)

	if weights:
		return pyservoce.bspline(
			pnts=pnts, 
			knots=knots,
			weights=weights,
			multiplicities=muls,
			degree=degree,
			periodic=periodic,
			check_rational=check_rational)
	else:
		return pyservoce.bspline(
			pnts=pnts, 
			knots=knots,
			multiplicities=muls,
			degree=degree,
			periodic=periodic)


@lazy.lazy(cls=shape_generator)
def rounded_polysegment(pnts, r):
    pnts = points(pnts)
    cpnts = pnts[1:-1]

    pairs = []
    pairs_tangs = []
    pairs.append((None, pnts[0]))

    for i in range(len(cpnts)):
        a = pyservoce.segment(pnts[i], pnts[i+1])
        b = pyservoce.segment(pnts[i+1], pnts[i+2])

        _, ad1 = a.d1(a.range()[1])
        _, bd1 = b.d1(b.range()[0])

        n = bd1.cross(ad1)

        if n.iszero():
            pairs.append((cpnts[i], cpnts[i]))
            pairs_tangs.append(None)
            continue

        abn = ad1.cross(n)
        bbn = bd1.cross(n)

        bn = (abn + bbn).normalize() * r

        c = cpnts[i] + bn

        ca = pyservoce.project(c, a)
        cb = pyservoce.project(c, b)

        pairs.append((ca,cb))
        pairs_tangs.append((ad1,bd1))

    pairs.append((pnts[-1], None))

    nodes = []
    for i in range(len(cpnts)):
        nodes.append(pyservoce.segment(pairs[i][1], pairs[i+1][0]))
        if pairs_tangs[i] is not None:
            nodes.append(pyservoce.interpolate(pnts=[pairs[i+1][0],pairs[i+1][1]], tang=[pairs_tangs[i][0],pairs_tangs[i][1]]))
    nodes.append(pyservoce.segment(pairs[-2][1], pairs[-1][0]))

    return pyservoce.make_wire(nodes)