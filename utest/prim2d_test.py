import unittest
import zencad

class Prim2dProbber(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True

	def test_rectangle_probber(self):
		x = 10
		y = 20
		a = 10
		zencad.rectangle(x, y, center=True, wire=True).unlazy()
		zencad.rectangle(a, center=True, wire=True).unlazy()
		zencad.rectangle(x, y, center=False, wire=True).unlazy()
		zencad.rectangle(a, center=False, wire=True).unlazy()
		zencad.rectangle(x, y, center=True, wire=False).unlazy()
		zencad.rectangle(a, center=True, wire=False).unlazy()
		zencad.rectangle(x, y, center=False, wire=False).unlazy()
		zencad.rectangle(a, center=False, wire=False).unlazy()

	def test_square_probber(self):
		a = 10
		zencad.square(a, center=True, wire=True).unlazy()
		zencad.square(a, center=True, wire=False).unlazy()
		zencad.square(a, center=False, wire=True).unlazy()
		zencad.square(a, center=False, wire=False).unlazy()
		
	def test_circle_probber(self):
		radius = 30
		angle = zencad.deg(45)
		start = zencad.deg(45)
		stop = zencad.deg(60)
		zencad.circle(r=radius, wire=True).unlazy()
		zencad.circle(r=radius, angle=angle, wire=True).unlazy()
		zencad.circle(r=radius, angle=(start, stop), wire=True).unlazy()
		zencad.circle(r=radius, wire=False).unlazy()
		zencad.circle(r=radius, angle=angle, wire=False).unlazy()
		zencad.circle(r=radius, angle=(start, stop), wire=False).unlazy()

	def test_ellipse_probber(self):
		radius = 50
		radius2 = 30
		angle = zencad.deg(45)
		start = zencad.deg(45)
		stop = zencad.deg(60)
		zencad.ellipse(r1=radius, r2=radius2, wire=True).unlazy()
		zencad.ellipse(r1=radius, r2=radius2, angle=angle, wire=True).unlazy()
		zencad.ellipse(r1=radius, r2=radius2, angle=(start, stop), wire=True).unlazy()
		zencad.ellipse(r1=radius, r2=radius2, wire=False).unlazy()
		zencad.ellipse(r1=radius, r2=radius2, angle=angle, wire=False).unlazy()
		zencad.ellipse(r1=radius, r2=radius2, angle=(start, stop), wire=False).unlazy()

		with self.assertRaises(Exception):
			zencad.ellipse(r1=radius2, r2=radius, wire=True).unlazy()

	def test_polygon_probber(self):
		pnts = [(0,0), (0,10), (10,0)]
		zencad.polygon(pnts=pnts, wire=True).unlazy()
		zencad.polygon(pnts=pnts, wire=False).unlazy()

	def test_ngon_probber(self):
		zencad.ngon(r=20, n=3, wire=True).unlazy()
		zencad.ngon(r=20, n=5, wire=True).unlazy()
		zencad.ngon(r=20, n=30, wire=True).unlazy()
		zencad.ngon(r=20, n=3, wire=False).unlazy()
		zencad.ngon(r=20, n=5, wire=False).unlazy()
		zencad.ngon(r=20, n=30, wire=False).unlazy()

	def test_textshape_probber(self):
		text="HelloWorld"
		zencad.textshape(text=text, fontpath="../zencad/examples/fonts/testfont.ttf", size=20).unlazy()
