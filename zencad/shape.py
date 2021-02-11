##!/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BinTools import BinTools_ShapeSet
from geom2.boolops import *
import trans
from lazifier2 import *

class Shape:
	def __init__(self, arg):
		if not isinstance(arg, TopoDS_Shape):
			raise Exception("Wrong Shape constructor invoke")

		self._shp = arg

	def __add__(self, oth):
		return Shape(occ_pair_union(self._shp, oth._shp))

	def __sub__(self, oth):
		return Shape(occ_pair_difference(self._shp, oth._shp))

	def __xor__(self, oth):
		return Shape(occ_pair_intersect(self._shp, oth._shp))

	def __getstate__(self):
		return { 
			"shape": self._shp, 
		}

	def __setstate__(self, dct):
		self._shp = dct["shape"]

	#@lazy.lazy(nocache=1)
	def transform(self, trans):
		shp = BRepBuilderAPI_Transform(self._shp, trans._trsf, True).Shape();
		return Shape(shp)

	@lazy.lazy(nocache=1)
	def move(self, *args): return trans.move(*args)(self)