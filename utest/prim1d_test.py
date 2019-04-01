import unittest
import zencad

class Prim1dProbber(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True

	def test_segment_probe(self):
		zencad.segment((0,0,0), (10,20,30)).unlazy()
		
	def test_polysegment_probe(self):
		pnts = [(0,0,0), (10,20,30), (10,21,35) , (10,22,40)]
		zencad.polysegment(pnts, closed=False).unlazy()
		zencad.polysegment(pnts, closed=True).unlazy()

	def test_interpolate_probe(self):
		pnts = [(0,0,0), (10,20,30), (10,21,35) , (10,22,40)]
		tang = [(0,0,1), (1,0,0), (0,1,0) , (0,0,0)]
		zencad.interpolate(pnts, closed=False).unlazy()
		zencad.interpolate(pnts, closed=True).unlazy()
		zencad.interpolate(pnts, tang, closed=False).unlazy()
		zencad.interpolate(pnts, tang, closed=True).unlazy()

	def test_circle_arc_probe(self):
		zencad.circle_arc((0,0), (1,1), (1,2)).unlazy() 

	def test_helix_probe(self):
		r=20
		h=20
		step=2
		angle=zencad.deg(15)
		zencad.helix(r, h, step, left=True)
		zencad.helix(r, h, step, angle=angle, left=True)
		zencad.helix(r, h, step, left=False)
		zencad.helix(r, h, step, angle=angle, left=False)
