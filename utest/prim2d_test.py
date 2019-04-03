import unittest
import zencad

class Prim2dprobe(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True

	def test_rectangle_probe(self):
		x = 10
		y = 20
		a = 10
		zencad.rectangle(x, y, center=True, wire=True)
		zencad.rectangle(a, center=True, wire=True)
		zencad.rectangle(x, y, center=False, wire=True)
		zencad.rectangle(a, center=False, wire=True)
		zencad.rectangle(x, y, center=True, wire=False)
		zencad.rectangle(a, center=True, wire=False)
		zencad.rectangle(x, y, center=False, wire=False)
		zencad.rectangle(a, center=False, wire=False)

	def test_square_probe(self):
		a = 10
		zencad.square(a, center=True, wire=True)
		zencad.square(a, center=True, wire=False)
		zencad.square(a, center=False, wire=True)
		zencad.square(a, center=False, wire=False)
		
	def test_circle_probe(self):
		radius = 30
		angle = zencad.deg(45)
		start = zencad.deg(45)
		stop = zencad.deg(60)
		zencad.circle(r=radius, wire=True)
		zencad.circle(r=radius, angle=angle, wire=True)
		zencad.circle(r=radius, angle=(start, stop), wire=True)
		zencad.circle(r=radius, wire=False)
		zencad.circle(r=radius, angle=angle, wire=False)
		zencad.circle(r=radius, angle=(start, stop), wire=False)

	def test_ellipse_probe(self):
		radius = 50
		radius2 = 30
		angle = zencad.deg(45)
		start = zencad.deg(45)
		stop = zencad.deg(60)
		zencad.ellipse(r1=radius, r2=radius2, wire=True)
		zencad.ellipse(r1=radius, r2=radius2, angle=angle, wire=True)
		zencad.ellipse(r1=radius, r2=radius2, angle=(start, stop), wire=True)
		zencad.ellipse(r1=radius, r2=radius2, wire=False)
		zencad.ellipse(r1=radius, r2=radius2, angle=angle, wire=False)
		zencad.ellipse(r1=radius, r2=radius2, angle=(start, stop), wire=False)

		with self.assertRaises(Exception):
			zencad.ellipse(r1=radius2, r2=radius, wire=True)

	def test_polygon_probe(self):
		pnts = [(0,0), (0,10), (10,0)]
		zencad.polygon(pnts=pnts, wire=True)
		zencad.polygon(pnts=pnts, wire=False)

	def test_ngon_probe(self):
		zencad.ngon(r=20, n=3, wire=True)
		zencad.ngon(r=20, n=5, wire=True)
		zencad.ngon(r=20, n=30, wire=True)
		zencad.ngon(r=20, n=3, wire=False)
		zencad.ngon(r=20, n=5, wire=False)
		zencad.ngon(r=20, n=30, wire=False)

	def test_textshape_probe(self):
		text="HelloWorld"
		zencad.textshape(text=text, fontpath="../zencad/examples/fonts/testfont.ttf", size=20)
