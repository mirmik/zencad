import unittest
import zencad


class Ops3dProbe(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_linear_extrude(self):
        proto = zencad.ngon(r=3, n=12)
        zencad.linear_extrude(proto, 3)
        zencad.linear_extrude(proto, zencad.vector3(3, 1, 3))

    def test_pipe(self):
        proto = zencad.circle(20)
        path = self._path()
        zencad.pipe(proto, path)

    def test_pipe_shell(self):
        proto0 = zencad.circle(20, wire=True)
        proto1 = zencad.circle(30, wire=True).up(10)
        proto2 = zencad.circle(30, wire=True).up(20)
        path = self._path()
        zencad.pipe_shell([proto0, proto1, proto2], path)
        zencad.pipe_shell([proto0], path, binormal=zencad.vector3(1, 0, 0))
        zencad.pipe_shell([proto0], path, parallel=zencad.vector3(1, 0, 0))

    @staticmethod
    def _path():
        return zencad.interpolate(
            tuple(
                zencad.point3(*value)
                for value in ((0, 0, 0), (0, 0, 10), (0, 10, 20))
            )
        )

    # def test_sweep(self):
    #    proto = zencad.circle(20, wire=True)
    #    path = zencad.interpolate([(0, 0, 0), (0, 0, 10), (0, 10, 20)])
    #    zencad.sweep(proto, path)
    #    zencad.sweep(proto=proto, path=path)

    def test_loft(self):
        arr = [
            zencad.circle(20, wire=True),
            zencad.circle(20, wire=True).up(10),
            zencad.square(20, wire=True, center=True).up(20),
        ]
        zencad.loft(arr)
        zencad.loft(arr, True)
        zencad.loft(sections=arr, smooth=True)

    def test_revol(self):
        zencad.revol(zencad.ngon(r=10, n=10).rotateX(zencad.deg(90)).right(30))
        zencad.revol(
            zencad.ngon(r=10, n=10).rotateX(zencad.deg(90)).right(30),
            yaw=zencad.deg(120),
        )

    def test_thinksolid(self):
        reference = zencad.point3(5, 0, 5)
        zencad.thicksolid(zencad.box(10), -1, [reference])
        zencad.thicksolid(zencad.box(10), 1, [reference])

    def test_shapefix_solid_downcasts_generic_shape(self):
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from zencad._native.offset import _shapefix_solid
        from zencad._native.shape import Shape

        generic_solid = Shape(BRepPrimAPI_MakeBox(2, 3, 4).Shape())
        fixed = _shapefix_solid(generic_solid)

        self.assertTrue(fixed.is_solid())
        self.assertAlmostEqual(fixed.mass(), 24.0)

    def test_fillet(self):
        zencad.box(20).fillet(1)
        reference = zencad.point3(5, 0, 0)
        zencad.box(20).fillet(1, [reference])
        zencad.fillet(zencad.box(20), 1, [reference])

    def test_chamfer(self):
        zencad.box(20).chamfer(1)
        reference = zencad.point3(5, 0, 0)
        zencad.box(20).chamfer(1, [reference])
        zencad.chamfer(zencad.box(20), 1, [reference])

    def test_ruled(self):
        zencad.ruled(
            zencad.segment(zencad.point3(0, 0, 0), zencad.point3(10, 10, 10)),
            zencad.segment(zencad.point3(10, 0, 0), zencad.point3(20, 10, 10)),
        )

    def test_triangulation(self):
        zencad.to_mesh(zencad.box(10), 0.1)
        zencad.triangulate(zencad.rectangle(10, 10), 0.1)
