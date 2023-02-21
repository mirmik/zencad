import unittest
import zencad


class MakeProbber(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_make_wire(self):
        s0 = zencad.wire.segment((0,0,0), (1,0,0))
        s1 = zencad.wire.segment((1,0,0), (1,1,0))
        s2 = zencad.wire.segment((1,1,0), (0,1,0))
        w = zencad.wire.make_wire([s0, s1, s2])

    def test_make_face(self):
        s0 = zencad.wire.segment((0,0,0), (1,0,0))
        s1 = zencad.wire.segment((1,0,0), (1,1,0))
        s2 = zencad.wire.segment((1,1,0), (0,1,0))
        s3 = zencad.wire.segment((0,1,0), (0,0,0))
        w = zencad.wire.make_wire([s0, s1, s2, s3])
        f = zencad.face.fill(w)

    def test_make_shell(self):
        sphere = zencad.sphere(10)
        face = sphere.faces()[0]   
        self.assertTrue(face.shapetype() == "face")
        shell = zencad.geom.shell.make_shell([face])