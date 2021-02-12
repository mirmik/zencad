from zencad.shape import Shape, nocached_shape_generator, shape_generator
from zencad.util3 import as_indexed
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

from OCC.Core.gp import gp_Pnt
from OCC.Core.GeomAPI import GeomAPI_Interpolate
from OCC.Core.TColgp import TColgp_HArray1OfPnt, TColgp_Array1OfVec
from OCC.Core.TColStd import TColStd_HArray1OfBoolean

from zencad.lazifier2 import *
from zencad.geom2.sew import sew
from zencad.util3 import points, to_Pnt, to_Vec

from zencad.geom2.project import project


import numpy

@lazy.lazy(cls=nocached_shape_generator)
def fill(shp):
	assert(shp.Shape().ShapeType() == TopAbs_WIRE);
	return Shape(BRepBuilderAPI_MakeFace(shp.Wire()).Face())

@lazy.lazy(cls=nocached_shape_generator)
def polysegment(pnts, closed=False):
	if len(pnts) <= 1:
		raise Exception("Need at least two points for polysegment");

	mkWire = BRepBuilderAPI_MakeWire()

	for i in range(len(pnts)-1):
		mkWire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(*pnts[i]), gp_Pnt(*pnts[i + 1])).Edge())

	if (closed):
		mkWire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(*pnts[len(pnts) - 1]), gp_Pnt(*pnts[0])).Edge())

	return Shape(mkWire.Wire())

@lazy.lazy(cls=nocached_shape_generator)
def polygon(pnts):
	return fill(polysegment(pnts, closed=True))

@lazy.lazy(cls=nocached_shape_generator)
def segment(a,b):
	a, b = points((a, b))
	return Shape(BRepBuilderAPI_MakeEdge(to_Pnt(a), to_Pnt(b)).Edge())

@lazy.lazy(cls=shape_generator)
def interpolate(pnts, tang=None, closed=False):
	print(pnts)
	print(tang)

	_pnts = TColgp_HArray1OfPnt(1, len(pnts))
	for i in range(len(pnts)):
		_pnts.SetValue(i + 1, gp_Pnt(*pnts[i]))

	algo = GeomAPI_Interpolate(_pnts, closed, 0.0000001);

	if tang is not None:
		if (len(tang) != 0):
			_tang = TColgp_Array1OfVec(1, len(tang))
			_bools = TColStd_HArray1OfBoolean(1, len(tang))
	
			for i in range(len(pnts)): _tang.SetValue(i + 1, to_Vec(tang[i]))
			for i in range(len(pnts)): 
				_bools.SetValue(i + 1, bool(numpy.linalg.norm(tang[i]) != 0))
	
			algo.Load(_tang, _bools);
		
	algo.Perform();
	return Shape(BRepBuilderAPI_MakeEdge(algo.Curve()).Edge())


@lazy.lazy(cls=shape_generator)
def rounded_polysegment(pnts, r, closed=False):
	# Для того, чтобы закрыть контур, не теряя скругления, перекрёстно добавляем две точки,
	# Две в начале, другую в конце.
	pnts = points(pnts)
	if closed:
		pnts.insert(0, pnts[-1])
		pnts.append(pnts[1])

	cpnts = pnts[1:-1]

	pairs = []
	pairs_tangs = []
	pairs.append((None, pnts[0]))

	print(000)
	for i in range(len(cpnts)):
		a = segment(pnts[i], pnts[i+1]).unlazy()
		b = segment(pnts[i+1], pnts[i+2]).unlazy()

		ad1 = a.d1(a.range()[1])
		bd1 = b.d1(b.range()[0])

		print(111)
		n = numpy.cross(bd1, ad1)

		if numpy.linalg.norm(n) == 0:
			pairs.append((cpnts[i], cpnts[i]))
			pairs_tangs.append(None)
			continue

		print(222)
		abn = numpy.cross(ad1,n)
		bbn = numpy.cross(bd1,n)

		temp = (abn + bbn)
		bn = temp/numpy.linalg.norm(temp) * r

		c = cpnts[i] + bn

		ca = project(c, a)
		cb = project(c, b)

		pairs.append((ca,cb))
		pairs_tangs.append((ad1,bd1))

	pairs.append((pnts[-1], None))

	nodes = []
	for i in range(len(cpnts)):
		nodes.append(segment(pairs[i][1], pairs[i+1][0]))
		if pairs_tangs[i] is not None:
			nodes.append(interpolate(pnts=[pairs[i+1][0],pairs[i+1][1]], tang=[pairs_tangs[i][0],pairs_tangs[i][1]]))
	nodes.append(segment(pairs[-2][1], pairs[-1][0]))

	# Для замыкания необходимо удалить крайние сегменты.
	if closed:
		del nodes[0]
		del nodes[-1]

	result = sew(nodes)

	# И, наконец, зашиваем прореху.
	if closed:
		result = sew([
			result,
			segment(result.endpoints()[0], result.endpoints()[1])
		])

	return result