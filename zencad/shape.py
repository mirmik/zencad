##!/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BinTools import BinTools_ShapeSet
from geom2.boolops import *
from lazifier2 import *

class Shape:
	def __init__(self, arg):
		if not isinstance(arg, TopoDS_Shape):
			raise Exception("Wrong Shape constructor invoke")

		self._shp = arg

	@lazy
	def __add__(self, oth):
		return Shape(occ_pair_union(self._shp, oth._shp))

	@lazy
	def __sub__(self, oth):
		return Shape(occ_pair_difference(self._shp, oth._shp))

	@lazy
	def __xor__(self, oth):
		return Shape(occ_pair_intersect(self._shp, oth._shp))

	@lazy
	def transform(self, trans):
		shp = BRepBuilderAPI_Transform(self._shp, trans._trsf, True).Shape();
		return Shape(shp)

	def __getstate__(self):
		return { 
			"shape": self._shp, 
		}

	def __setstate__(self, dct):
		self._shp = dct["shape"]
