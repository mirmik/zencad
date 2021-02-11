##!/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BinTools import BinTools_ShapeSet
from geom2.boolops import *
import trans
from lazifier2 import *

class Shape:
	""" Basic zencad type. """

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

	def transform(self, trans):
		shp = BRepBuilderAPI_Transform(self._shp, trans._trsf, True).Shape()
		return Shape(shp)

	def move(self, *args): return trans.move(*args)(self)
	def moveX(self, *args): return trans.moveX(*args)(self)
	def moveY(self, *args): return trans.moveY(*args)(self)
	def moveZ(self, *args): return trans.moveZ(*args)(self)

	def translate(self, *args): return trans.translate(*args)(self)
	def translateX(self, *args): return trans.translateX(*args)(self)
	def translateY(self, *args): return trans.translateY(*args)(self)
	def translateZ(self, *args): return trans.translateZ(*args)(self)

	def rotate(self, *args): return trans.rotate(*args)(self)
	def rotateX(self, *args): return trans.rotateX(*args)(self)
	def rotateY(self, *args): return trans.rotateY(*args)(self)
	def rotateZ(self, *args): return trans.rotateZ(*args)(self)

	def scale(self, *args): return trans.scale(*args)(self)
	def scaleX(self, *args): return trans.scaleX(*args)(self)
	def scaleY(self, *args): return trans.scaleY(*args)(self)
	def scaleZ(self, *args): return trans.scaleZ(*args)(self)
	def scaleXYZ(self, *args): return trans.scaleXYZ(*args)(self)

	def up(self, *args): return trans.up(*args)(self)
	def down(self, *args): return trans.down(*args)(self)
	def right(self, *args): return trans.right(*args)(self)
	def left(self, *args): return trans.left(*args)(self)
	def forw(self, *args): return trans.forw(*args)(self)
	def back(self, *args): return trans.back(*args)(self)

	def mirror(self, *args): return trans.mirror(*args)(self)
	def mirrorX(self, *args): return trans.mirrorX(*args)(self)
	def mirrorY(self, *args): return trans.mirrorY(*args)(self)
	def mirrorZ(self, *args): return trans.mirrorZ(*args)(self)
	def mirrorXY(self, *args): return trans.mirrorXY(*args)(self)
	def mirrorXZ(self, *args): return trans.mirrorXZ(*args)(self)
	def mirrorYZ(self, *args): return trans.mirrorYZ(*args)(self)

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

A = set(Shape.__dict__.keys())
B = set(LazyObjectShape.__dict__.keys())

C = B.difference(A).difference({
	"cached_methods", "nocached_methods", "unlazy", "_generic"
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