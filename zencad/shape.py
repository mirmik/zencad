##!/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BinTools import BinTools_ShapeSet
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire
from OCC.Core.TopoDS import topods

from zencad.geom2.boolops_base import *
from zencad.lazifier2 import *
import zencad.trans
import zencad.transformed

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
			return Wire();
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

	def _generic(name, cached):
		def foo(self, *args, **kwargs):
			return self.lazyinvoke(
				getattr(Shape, name),
				(self, *args),
				kwargs,
				cached=cached,
				cls=LazyObjectShape,
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
		"scaleX", "scaleY", "scaleZ", "scaleXYZ"
	]

	nocached_methods = [
		"up", "down", "left", "right", "forw", "back",
		"move", "moveX", "moveY", "moveZ",
		"translate", "translateX", "translateY", "translateZ",
		"rotate", "rotateX", "rotateY", "rotateZ",
		"mirror", "mirrorX", "mirrorY", "mirrorZ",
		"mirrorYZ", "mirrorXY", "mirrorXZ",
		"scale", "transform",

		#"props1", "props2", "props3"	
	]

for item in LazyObjectShape.nolazy_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic_unlazy(item))

for item in LazyObjectShape.nocached_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic(item, False))

for item in LazyObjectShape.cached_methods:
	setattr(LazyObjectShape, item, LazyObjectShape._generic(item, True))


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
	"cached_methods", "nocached_methods", "unlazy", "_generic", "_generic_unlazy", "nolazy_methods"
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