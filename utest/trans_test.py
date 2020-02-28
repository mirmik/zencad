import unittest
import zencad
import math

def early(a, b):
    if abs(a.x - b.x) > 0.0001:
        return False
    if abs(a.y - b.y) > 0.0001:
        return False
    if abs(a.z - b.z) > 0.0001:
        return False
    return True

class TransformationProbe(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache = False
		zencad.lazy.decache = False
		zencad.lazy.fastdo = True

	def test_translate(self):
		x = 10
		y = 20
		z = 30
		v = 10

		pnt = zencad.point(x,y,z)

		self.assertEqual( zencad.translate(z,y,x)(pnt), zencad.point(40,40,40) )

		self.assertEqual( zencad.up(v)(pnt), zencad.point(x,y,z+v) )
		self.assertEqual( zencad.down(v)(pnt), zencad.point(x,y,z-v) )
		self.assertEqual( zencad.left(v)(pnt), zencad.point(x-v,y,z) )
		self.assertEqual( zencad.right(v)(pnt), zencad.point(x+v,y,z) )
		self.assertEqual( zencad.forw(v)(pnt), zencad.point(x,y+v,z) )
		self.assertEqual( zencad.back(v)(pnt), zencad.point(x,y-v,z) )

		self.assertEqual( zencad.moveX(v)(pnt), zencad.point(x+v,y,z) )
		self.assertEqual( zencad.moveY(v)(pnt), zencad.point(x,y+v,z) )
		self.assertEqual( zencad.moveZ(v)(pnt), zencad.point(x,y,z+v) )

	def test_rotate(self):
		x = 10
		y = 20
		z = 30
		v = 10

		pnt = zencad.point(x,y,z)

		ang = zencad.deg(v)
		self.assertEqual(
			zencad.rotateX(ang)(pnt),
			zencad.point(
				x,
				y*math.cos(ang)-z*math.sin(ang), 
				z*math.cos(ang)+y*math.sin(ang))
		)

		self.assertEqual(
			zencad.rotateY(ang)(pnt),
			zencad.point(
				x*math.cos(ang)+z*math.sin(ang), 
				y,
				z*math.cos(ang)-x*math.sin(ang))
		)

		self.assertEqual( 
			zencad.rotateZ(ang)(pnt),
			zencad.point(
				x*math.cos(ang)-y*math.sin(ang), 
				y*math.cos(ang)+x*math.sin(ang),
				z)
		)

	def test_trans_shape(self):
		x = 10
		y = 20
		z = 30
		v = 10

		box = zencad.box(10,10,10,center=True).translate(x,y,z)

		self.assertEqual( (zencad.translate(z,y,x)(box)).center().unlazy(), zencad.point(40,40,40) )

	def test_short_rotate(self):
		t = zencad.short_rotate((1,0,0))

		m = zencad.point3(0,0,1)
		m = t(m)

		self.assertEqual(m, zencad.point3(1,0,0))


