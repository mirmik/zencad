##!/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Vertex
from OCC.Core.BinTools import BinTools_ShapeSet
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.TopoDS import topods
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.TopExp import topexp, TopExp_Explorer

from zencad.geom2.boolops_base import *
from zencad.lazifier2 import *
import zencad.trans
import zencad.transformed
from zencad.util3 import to_numpy

import numpy

class Shape(zencad.transformed.Transformed):
	""" Basic zencad type. """

	def __init__(self, arg):
		if not isinstance(arg, TopoDS_Shape):
			raise Exception("Wrong Shape constructor invoke")

		self._shp = arg

	def Shape(self): return self._shp
	def Wire(self):  return topods.Wire(self._shp)
	def Edge(self):  return topods.Edge(self._shp)
	def Vertex(self):  return topods.Vertex(self._shp)
	def Shell(self):  return topods.Shell(self._shp)
	def Solid(self):  return topods.Solid(self._shp)
	def Compound(self):  return topods.Compound(self._shp)
	def CompSolid(self):  return topods.CompSolid(self._shp)

	def Wire_orEdgeToWire(self):
		if (self.Shape().ShapeType() == TopAbs_WIRE):
			return self.Wire();
		else:
			return BRepBuilderAPI_MakeWire(self.Edge()).Wire();

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

	def transform(self, trans):
		shp = BRepBuilderAPI_Transform(self._shp, trans._trsf, True).Shape()
		return Shape(shp)

	def is_wire(self): return self.Shape().ShapeType() == TopAbs_WIRE
	def is_edge(self): return self.Shape().ShapeType() == TopAbs_EDGE
	def is_face(self): return self.Shape().ShapeType() == TopAbs_FACE
	def is_solid(self): return self.Shape().ShapeType() == TopAbs_SOLID
	def is_compound(self): return self.Shape().ShapeType() == TopAbs_COMPOUND
	def is_compsolid(self): return self.Shape().ShapeType() == TopAbs_COMPSOLID
	def is_shell(self): return self.Shape().ShapeType() == TopAbs_SHELL
	def is_vertex(self): return self.Shape().ShapeType() == TopAbs_VERTEX
	def is_wire_or_edge(self): return self.is_edge() or self.is_wire()


	def edges(self):
		ret = []

		ex = TopExp_Explorer(self.Shape(), TopAbs_EDGE)
		while ex.More():
			obj = topods.Edge(ex.Current())
			ret.append(Shape(obj))
			ex.Next()

		return ret;

	def fill(self):
		assert(self.is_wire_or_edge())
		return Shape(BRepBuilderAPI_MakeFace(self.Wire()).Face())

	# TODO: Вынести в curve_algo
	def AdaptorCurve(self):
		assert(self.is_edge())
		return BRepAdaptor_Curve(self.Edge())		

	def d1(self, arg):
		assert(self.is_edge())
		adaptor = self.AdaptorCurve()
		pnt, vec = gp_Pnt(), gp_Vec()
		self.AdaptorCurve().D1(arg, pnt, vec)
		return numpy.array((vec.X(), vec.Y(), vec.Z()))

	def range(self):
		adaptor = self.AdaptorCurve()
		return adaptor.FirstParameter(), adaptor.LastParameter()

	def endpoints(self):
		assert(self.is_wire_or_edge())

		if self.is_wire():
			a, b = TopoDS_Vertex(), TopoDS_Vertex()
			topexp.Vertices(self.Wire(), a, b);
			return to_numpy(a), to_numpy(b)
	
		elif self.is_edge():
			a = topexp.FirstVertex(self.Edge())
			b = topexp.LastVertex(self.Edge())
			return to_numpy(a), to_numpy(b)


	def Curve(self):
		aCurve = BRep_Tool.Curve(self.Edge())
		return aCurve[0];		

# Support lazy methods
class LazyObjectShape(evalcache.LazyObject):
	""" Lazy object specification for Shape class.
		It control methods lazyfying. And add some checks.
		All Shapes wrappers must use LazyShapeObject. 
	"""

	def __init__(self, *args, **kwargs):
		evalcache.LazyObject.__init__(self, *args, **kwargs)

	def unlazy(self):
		"""Test wrapped object type equality."""
		obj = super().unlazy()
		if not isinstance(obj, Shape):
			raise Exception(f"LazyObjectShape wraped type is not Shape: class:{obj.__class__}")
		return obj

	def _generic(name, cached, cls):
		def foo(self, *args, **kwargs):
			return self.lazyinvoke(
				getattr(Shape, name),
				(self, *args),
				kwargs,
				cached=cached,
				cls=cls,
			)	

		return foo

	def _generic_unlazy(name):
		def foo(self, *args, **kwargs):
			return getattr(Shape, name)(self.unlazy(), *args, **kwargs)
		return foo

	nolazy_methods = [
		"Shape", "Vertex", "Wire", "Edge", "Solid", "Compound", "Shell", "CompSolid", "Wire_orEdgeToWire"
	]

	cached_methods = [
		"__add__", "__sub__", "__xor__",
		"scaleX", "scaleY", "scaleZ", "scaleXYZ", "fill"
	]

	nocached_methods = [
		"up", "down", "left", "right", "forw", "back",
		"move", "moveX", "moveY", "moveZ",
		"mov", "movX", "movY", "movZ",
		"translate", "translateX", "translateY", "translateZ",
		"rotate", "rotateX", "rotateY", "rotateZ",
		"rot", "rotX", "rotY", "rotZ",
		"mirror", "mirrorX", "mirrorY", "mirrorZ",
		"mirrorYZ", "mirrorXY", "mirrorXZ",
		"scale", "transform",

		#"props1", "props2", "props3"	
	]

	standart_methods = [
		"is_wire", "is_compsolid", "is_edge", "is_face", "is_shell", "is_wire_or_edge", "is_solid"
	]

for item in LazyObjectShape.nocached_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic(item, False, cls=LazyObjectShape))

for item in LazyObjectShape.nolazy_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic_unlazy(item))

for item in LazyObjectShape.standart_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic(item, False, cls=evalcache.LazyObject))

for item in LazyObjectShape.cached_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic(item, True, cls=LazyObjectShape))


class nocached_shape_generator(evalcache.LazyObject):
	"""	Decorator for heavy functions.
		It use caching for lazy data restoring."""

	def __init__(self, *args, **kwargs):
		evalcache.LazyObject.__init__(self, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.lazyinvoke(
			self, args, kwargs, encache=False, decache=False, cls=LazyObjectShape
		)

class shape_generator(evalcache.LazyObject):
	"""	Decorator for lightweight functions.
		It prevent caching."""
	
	def __init__(self, *args, **kwargs):
		evalcache.LazyObject.__init__(self, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.lazyinvoke(self, args, kwargs, cls=LazyObjectShape)

A = ( 
	set(Shape.__dict__.keys()).union(
	set(zencad.transformed.Transformed.__dict__.keys())))

B = set(LazyObjectShape.__dict__.keys())

C = B.difference(A).difference({
	"cached_methods", "standart_methods", "nocached_methods", "unlazy", "_generic", "_generic_unlazy", "nolazy_methods"
})

D = A.difference(B).difference({
	"__dict__", "__weakref__", "__getstate__", "__setstate__"
})

if len(D) != 0:
	print("Warning: LazyShapeObject has not wrappers for methods:")
	print(D)

if len(C) != 0:
	print("Warning: LazyShapeObject has wrappers for unexisted methods:")
	print(C)