import unittest
import zencad
import evalcache

from functools import cmp_to_key

def lexsort(a):
    a = evalcache.unlazy_if_need(a)

    def comparator(a,b):
        return 1 if a > b else -1 

    return sorted(a, key=cmp_to_key(comparator))


class Prim3dprobe(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_box_probe(self):
        a = zencad.box(10, 10, 10)
        b = zencad.box(size=(10, 10, 10))
        c = zencad.box(10)
        self.assertEqual(lexsort(a.vertices()), lexsort(b.vertices()))
        self.assertEqual(lexsort(c.vertices()), lexsort(b.vertices()))

        a = zencad.box(10, 10, 10, center=True)
        b = zencad.box(size=(10, 10, 10), center=True)
        c = zencad.box(10, center=True)
        self.assertEqual(lexsort(a.vertices()), lexsort(b.vertices()))
        self.assertEqual(lexsort(c.vertices()), lexsort(b.vertices()))

        a = zencad.cube(10, 10, 10, True)
        b = zencad.cube(10, 10, 10, center=True)
        c = zencad.cube(size=(10, 10, 10), center=True)
        d = zencad.cube(10, center=True)

    def test_sphere_probe(self):
        radius = 20
        minPitch = zencad.deg(-10)
        maxPitch = zencad.deg(20)
        yaw = zencad.deg(130)

        zencad.sphere(r=radius)
        zencad.sphere(r=radius, yaw=yaw)
        zencad.sphere(r=radius, pitch=(minPitch, maxPitch))
        zencad.sphere(r=radius, yaw=yaw, pitch=maxPitch)
        zencad.sphere(r=radius, yaw=yaw, pitch=(minPitch, maxPitch))

    def test_cylinder_probe(self):
        radius = 20
        height = 30
        yaw = zencad.deg(130)
        zencad.cylinder(r=radius, h=height, center=True)
        zencad.cylinder(r=radius, h=height, yaw=yaw, center=True)
        zencad.cylinder(r=radius, h=height, center=False)
        zencad.cylinder(r=radius, h=height, yaw=yaw, center=False)

    def test_cone_probe(self):
        topRadius = 20
        botRadius = 10
        height = 30
        yaw = zencad.deg(130)

        zencad.cone(r1=botRadius, r2=topRadius, h=height, center=True)
        zencad.cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=True)
        zencad.cone(r1=0, r2=topRadius, h=height, center=True)
        zencad.cone(r1=botRadius, r2=0, h=height, center=True)

        zencad.cone(r1=botRadius, r2=topRadius, h=height, center=False)
        zencad.cone(r1=botRadius, r2=topRadius,
                    h=height, yaw=yaw, center=False)
        zencad.cone(r1=0, r2=topRadius, h=height, center=False)
        zencad.cone(r1=botRadius, r2=0, h=height, center=False)

    def test_torus_probe(self):
        centralRadius = 20
        localRadius = 3
        yaw = zencad.deg(130)

        minPitch = zencad.deg(-10)
        maxPitch = zencad.deg(20)

        zencad.torus(r1=centralRadius, r2=localRadius)
        zencad.torus(r1=centralRadius, r2=localRadius, yaw=yaw)
        zencad.torus(r1=centralRadius, r2=localRadius,
                     pitch=(minPitch, maxPitch))
        zencad.torus(
            r1=centralRadius, r2=localRadius, yaw=yaw, pitch=(
                minPitch, maxPitch)
        )
        zencad.torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=maxPitch)

    def test_halfspace_probe(self):
        (zencad.sphere(r=10) - zencad.halfspace().rotateX(zencad.deg(150)))
        (zencad.sphere(r=10) ^ zencad.halfspace().rotateX(zencad.deg(150)))
