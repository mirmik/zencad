import math
import unittest

import zencad
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound


class CompactMeshTest(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_box_preserves_sharp_normals(self):
        mesh = zencad.to_mesh(zencad.box(10))

        self.assertEqual(mesh.triangle_count, 12)
        self.assertEqual(mesh.vertex_count, 24)
        self.assertEqual(len(mesh.triangle_face_ids), 12)
        self.assertEqual(mesh.dropped_triangles, 0)

    def test_transformation_is_applied(self):
        mesh = zencad.to_mesh(zencad.box(2).translate(10, 20, 30))
        xs, ys, zs = zip(*mesh.positions)

        self.assertAlmostEqual(min(xs), 10)
        self.assertAlmostEqual(max(xs), 12)
        self.assertAlmostEqual(min(ys), 20)
        self.assertAlmostEqual(max(ys), 22)
        self.assertAlmostEqual(min(zs), 30)
        self.assertAlmostEqual(max(zs), 32)

    def test_normals_are_normalized(self):
        mesh = zencad.to_mesh(zencad.sphere(10))
        for normal in mesh.normals:
            length = math.sqrt(sum(component * component for component in normal))
            self.assertAlmostEqual(length, 1.0)

    def test_triangle_winding_agrees_with_normals(self):
        mesh = zencad.to_mesh(zencad.box(10))
        for triangle in mesh.triangles:
            a, b, c = (mesh.positions[index] for index in triangle)
            ab = tuple(b[index] - a[index] for index in range(3))
            ac = tuple(c[index] - a[index] for index in range(3))
            cross = (
                ab[1] * ac[2] - ab[2] * ac[1],
                ab[2] * ac[0] - ab[0] * ac[2],
                ab[0] * ac[1] - ab[1] * ac[0],
            )
            dot = sum(
                cross[index] * mesh.normals[triangle[0]][index]
                for index in range(3)
            )
            self.assertGreater(dot, 0)

    def test_angular_deflection_controls_density(self):
        shape = zencad.torus(20, 5)
        fine = zencad.to_mesh(shape, 0.5, 0.4)
        coarse = zencad.to_mesh(shape, 0.5, 0.8)

        self.assertLess(coarse.triangle_count, fine.triangle_count)

    def test_weld_tolerance_spans_neighboring_hash_cells(self):
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        builder.Add(compound, zencad.box(1).unlazy().Shape())
        builder.Add(
            compound,
            zencad.box(1).translate(1.0009, 0, 0).unlazy().Shape(),
        )

        separate = zencad.to_mesh(zencad.Shape(compound), weld_tolerance=0.0005)
        welded = zencad.to_mesh(zencad.Shape(compound), weld_tolerance=0.001)

        self.assertEqual(separate.vertex_count, 48)
        self.assertEqual(welded.vertex_count, 40)
        self.assertEqual(welded.triangle_count, separate.triangle_count)

    def test_invalid_tolerances_are_rejected(self):
        with self.assertRaises(ValueError):
            zencad.to_mesh(zencad.box(1), linear_deflection=0)
        with self.assertRaises(ValueError):
            zencad.to_mesh(zencad.box(1), angular_deflection=0)
        with self.assertRaises(ValueError):
            zencad.to_mesh(zencad.box(1), crease_angle=-0.1)
        with self.assertRaises(ValueError):
            zencad.to_mesh(zencad.box(1), weld_tolerance=math.inf)
        with self.assertRaises(ValueError):
            zencad.to_mesh(zencad.box(1), crease_angle=math.nan)


if __name__ == "__main__":
    unittest.main()
