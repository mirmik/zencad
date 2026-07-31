import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import zencad
from zencad.convert.api import _from_brep, _to_brep, _to_stl


def unlazy(value):
    return value.unlazy() if hasattr(value, "unlazy") else value


class MigrationBaseline(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_primitive_mass_and_topology(self):
        box = zencad.box(20, center=True)

        self.assertAlmostEqual(unlazy(box.mass()), 8000.0, places=8)
        self.assertEqual(len(box.faces()), 6)
        self.assertEqual(len(box.edges()), 24)
        self.assertEqual(len(box.vertices()), 8)
        self.assertEqual(len(box.solids()), 1)

        sphere = zencad.sphere(5)
        self.assertAlmostEqual(
            unlazy(sphere.mass()),
            4.0 * math.pi * 5.0**3 / 3.0,
            places=8,
        )
        self.assertEqual(len(sphere.faces()), 1)
        self.assertEqual(len(sphere.solids()), 1)

    def test_transform_center_and_bounds(self):
        shape = zencad.box(20, center=True).translate(3, -4, 5)
        center = unlazy(shape.center())
        bounds = unlazy(shape.bbox())

        self.assertAlmostEqual(center.x, 3.0, places=8)
        self.assertAlmostEqual(center.y, -4.0, places=8)
        self.assertAlmostEqual(center.z, 5.0, places=8)
        self.assertAlmostEqual(bounds.xmin, -7.0, places=6)
        self.assertAlmostEqual(bounds.xmax, 13.0, places=6)
        self.assertAlmostEqual(bounds.ymin, -14.0, places=6)
        self.assertAlmostEqual(bounds.ymax, 6.0, places=6)
        self.assertAlmostEqual(bounds.zmin, -5.0, places=6)
        self.assertAlmostEqual(bounds.zmax, 15.0, places=6)

    def test_boolean_difference_contract(self):
        shape = zencad.box(20, center=True) - zencad.sphere(5)
        expected = 8000.0 - 4.0 * math.pi * 5.0**3 / 3.0

        self.assertAlmostEqual(unlazy(shape.mass()), expected, places=8)
        self.assertEqual(len(shape.faces()), 7)
        self.assertEqual(len(shape.solids()), 1)

    def test_brep_round_trip_and_stl_export(self):
        source = zencad.box(20, center=True) - zencad.sphere(5)

        with TemporaryDirectory() as temporary_directory:
            brep_path = Path(temporary_directory) / "shape.brep"
            stl_path = Path(temporary_directory) / "shape.stl"

            _to_brep(unlazy(source), str(brep_path))
            restored = _from_brep(str(brep_path))
            self.assertAlmostEqual(
                unlazy(restored.mass()),
                unlazy(source.mass()),
                places=8,
            )
            self.assertEqual(len(restored.faces()), len(source.faces()))

            self.assertTrue(_to_stl(unlazy(source), str(stl_path), 0.1))
            self.assertGreater(stl_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
