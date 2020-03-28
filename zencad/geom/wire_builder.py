from zencad.util import point3, vector3
from zencad.geom.prim1d import *
from zencad.geom.ops1d2d import *

class wire_builder:
	def __init__(self, start = (0,0,0), defrel=False):
		self.edges = []
		self.current = point3(start)
		self.start = self.current
		self.default_rel = defrel

	def restart(self, pnt, y=None, z=None):
		pnt = self.collect_point(pnt, y, z)
		self.edges = []
		self.current = point3(pnt)
		self.start = self.current
		return self

	@staticmethod
	def collect_point(pnt,y,z):
		if z is not None:
			pnt = (pnt,y,z)
		elif y is not None:
			pnt = (pnt,y)	
		return pnt

	def prepare(self, pnts, rel):
		if rel is None:
			rel = self.default_rel

		if rel is False:
			return points(pnts)
		else:
			return [ self.current + vector3(p) for p in pnts ]

	def segment(self,pnt,y=None,z=None,rel=None):
		pnt = self.collect_point(pnt, y, z)
		target, = self.prepare([pnt], rel)
		self.edges.append(segment(self.current, target))
		self.current = target
		return self

	def line(self, *args, **kwargs):
		return self.segment(*args, **kwargs)

	def l(self, *args, **kwargs):
		return self.segment(*args, **kwargs)

	def close(self, approx_a=False, approx_b=False):
		if approx_a is None and approx_b is None: 
			self.edges.append(segment(self.current, self.start))
		
		else:
			tanga= (0,0,0)
			tangb= (0,0,0)

			if approx_a:
				_, tanga = self.edges[-1].d1(self.edges[-1].range()[1])
			
			if approx_b:
				_, tangb = self.edges[0].d1(self.edges[0].range()[0])

			self.edges.append(interpolate([self.current, self.start], [tanga, tangb]))

		return self

	def arc_by_points(self, a, b, rel=None):
		a, b = self.prepare([a,b], rel)
		self.edges.append(circle_arc(self.current, a, b))
		self.current = b
		return self

	def interpolate(self, pnts, tangs=None, curtang=(0,0,0), approx=False, rel=None):
		if tangs is None:
			tangs = [(0,0,0)] * len(pnts)

		if approx:
			cc, fintang = self.edges[-1].d1(self.edges[-1].range()[1])
			curtang = fintang

		pnts= self.prepare(pnts, rel)
		pnts = points([self.current] + pnts)
		tangs = vectors([curtang] + tangs)
		print(tangs)

		self.edges.append(interpolate(pnts=pnts, tangs=tangs))
		self.current = pnts[-1]
		return self

	def doit(self):
		return sew(self.edges)