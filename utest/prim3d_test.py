import unittest
import zencad

class Prim3dprobe(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True

	def test_box_probe(self):
		a=zencad.box(10,10,10).unlazy()
		b=zencad.box(size=(10,10,10)).unlazy()
		c=zencad.box(10).unlazy()
		self.assertEqual(a.vertices(), b.vertices())
		self.assertEqual(c.vertices(), b.vertices())
		
		a=zencad.box(10,10,10, center=True).unlazy()
		b=zencad.box(size=(10,10,10), center=True).unlazy()
		c=zencad.box(10, center=True).unlazy()
		self.assertEqual(a.vertices(), b.vertices())
		self.assertEqual(c.vertices(), b.vertices())

		a=zencad.cube(10,10,10,True).unlazy()
		b=zencad.cube(10,10,10, center=True).unlazy()
		c=zencad.cube(size=(10,10,10), center=True).unlazy()
		d=zencad.cube(10, center=True).unlazy()

	def test_sphere_probe(self):
		radius = 20
		minPitch = zencad.deg(-10) 
		maxPitch = zencad.deg(20)
		yaw = zencad.deg(130)

		zencad.sphere(r=radius).unlazy()
		zencad.sphere(r=radius, yaw=yaw).unlazy()
		zencad.sphere(r=radius, pitch=(minPitch, maxPitch)).unlazy()
		zencad.sphere(r=radius, yaw=yaw, pitch=maxPitch).unlazy()
		zencad.sphere(r=radius, yaw=yaw, pitch=(minPitch, maxPitch)).unlazy()

	def test_cylinder_probe(self):
		radius = 20
		height = 30
		yaw = zencad.deg(130)
		zencad.cylinder(r=radius, h=height, center=True).unlazy()
		zencad.cylinder(r=radius, h=height, yaw=yaw, center=True).unlazy()
		zencad.cylinder(r=radius, h=height, center=False).unlazy()
		zencad.cylinder(r=radius, h=height, yaw=yaw, center=False).unlazy()

	def test_cone_probe(self):
		topRadius=20
		botRadius=10
		height=30
		yaw=zencad.deg(130)

		zencad.cone(r1=botRadius, r2=topRadius, h=height, center=True).unlazy()
		zencad.cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=True).unlazy()
		zencad.cone(r1=0, r2=topRadius, h=height, center=True).unlazy()
		zencad.cone(r1=botRadius, r2=0, h=height, center=True).unlazy()

		zencad.cone(r1=botRadius, r2=topRadius, h=height, center=False).unlazy()
		zencad.cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=False).unlazy()
		zencad.cone(r1=0, r2=topRadius, h=height, center=False).unlazy()
		zencad.cone(r1=botRadius, r2=0, h=height, center=False).unlazy()

	def test_torus_probe(self):
		centralRadius = 20
		localRadius = 3
		yaw=zencad.deg(130)

		minPitch = zencad.deg(-10) 
		maxPitch = zencad.deg(20)

		zencad.torus(r1=centralRadius, r2=localRadius).unlazy()
		zencad.torus(r1=centralRadius, r2=localRadius, yaw=yaw).unlazy()
		zencad.torus(r1=centralRadius, r2=localRadius, pitch=(minPitch, maxPitch)).unlazy()
		zencad.torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=(minPitch, maxPitch)).unlazy()
		zencad.torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=maxPitch).unlazy()

	def test_halfspace_probe(self):
		(zencad.sphere(r=10) - zencad.halfspace().rotateX(zencad.deg(150))).unlazy()
		(zencad.sphere(r=10) ^ zencad.halfspace().rotateX(zencad.deg(150))).unlazy()

	def test_union_probe(self):
		a = zencad.box(10)
		b = zencad.sphere(10)
		c = zencad.cone(5,2,h=20)

		f1 = zencad.union([a,b,c])
		f2 = (a + b + c)
		f3 = zencad.union([c,a,b])
		f4 = (c + a + b)

		self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
		self.assertEqual(f1.vertices().unlazy(), f3.vertices().unlazy())
		self.assertEqual(f1.vertices().unlazy(), f4.vertices().unlazy())

	def test_intersect_probe(self):
		a = zencad.box(10)
		b = zencad.sphere(10)
		c = zencad.cone(5,2,h=20)

		f1 = zencad.intersect([a,b,c])
		f2 = (a ^ b ^ c)
		f3 = zencad.intersect([c,a,b])
		f4 = (c ^ a ^ b)

		self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
		self.assertEqual(f1.vertices().unlazy(), f3.vertices().unlazy())
		self.assertEqual(f1.vertices().unlazy(), f4.vertices().unlazy())


	def test_difference_probe(self):
		a = zencad.box(10)
		b = zencad.sphere(10)
		c = zencad.cone(5,2,h=20)

		f1 = zencad.difference([a,b,c])
		f2 = (a - b - c)
		f3 = zencad.difference([c,a,b])
		f4 = (c - a - b)

		self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
		self.assertEqual(f3.vertices().unlazy(), f4.vertices().unlazy())

