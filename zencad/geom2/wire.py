from zencad.shape import Shape, nocached_shape_generator
from util3 import as_indexed
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

from OCC.Core.gp import gp_Pnt

from zencad.lazifier2 import *

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
	return Shape(BRepBuilderAPI_MakeEdge(gp_Pnt(*a), gp_Pnt(*b)).Edge())

