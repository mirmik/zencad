from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
import evalcache

class Curve:
	def __init__(self, crv):
		self._crv = crv

	def Curve(self):
		return self._crv

	# TODO: Add unlazy wrapper
	def edge(self, interval=None):
		import zencad.geom.wire
		return zencad.geom.wire.make_edge(self, interval)

class nocached_curve_generator(evalcache.LazyObject):
	"""	Decorator for heavy functions.
		It use caching for lazy data restoring."""

	def __init__(self, *args, **kwargs):
		evalcache.LazyObject.__init__(self, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.lazyinvoke(
			self, args, kwargs, 
			encache=False, 
			decache=False, 
			cls=evalcache.LazyObject
		)
