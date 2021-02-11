from shape import Shape, nocached_shape_generator, shape_generator
from util3 import as_indexed
import OCC.Core.BRepPrimAPI
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.TopAbs import TopAbs_WIRE

from lazifier2 import *

import geom2.wire

@lazy.lazy(cls=shape_generator)
def fill(shp):
	assert(shp.Shape().ShapeType() == TopAbs_WIRE);
	return Shape(BRepBuilderAPI_MakeFace(shp.Wire()).Face())

def polygon(pnts):
	return fill(geom2.wire.polysegment(pnts, closed=True))
