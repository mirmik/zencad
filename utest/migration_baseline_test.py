import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import evalcache.dircache_v2
import zencad
from OCP.TopoDS import TopoDS_Shape
from zencad.convert.api import _from_brep, _to_brep, _to_stl
from zencad.geombase import point3, vector3
from zencad.geom.curve import Curve, circle as curve_circle
from zencad.geom.curve2 import Curve2, ellipse as curve2_ellipse
from zencad.geom.shape import LazyObjectShape, Shape
from zencad.geom.surface import Surface, cylinder as cylinder_surface


def unlazy(value):
    return value.unlazy() if hasattr(value, "unlazy") else value


class MigrationBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_cache = zencad.lazy.cache
        cls.cache_directory = TemporaryDirectory()
        zencad.lazy.cache = evalcache.dircache_v2.DirCache_v2(
            cls.cache_directory.name
        )

    @classmethod
    def tearDownClass(cls):
        zencad.lazy.cache = cls.previous_cache
        cls.cache_directory.cleanup()

    def setUp(self):
        self.previous_policy = (
            zencad.lazy.encache,
            zencad.lazy.decache,
            zencad.lazy.fastdo,
            zencad.lazy.onplace,
        )
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True
        zencad.lazy.onplace = False

    def tearDown(self):
        (
            zencad.lazy.encache,
            zencad.lazy.decache,
            zencad.lazy.fastdo,
            zencad.lazy.onplace,
        ) = self.previous_policy

    def test_lazy_and_onplace_use_different_runtime_type_worlds(self):
        lazy_box = zencad.box(2)

        self.assertIs(type(lazy_box), LazyObjectShape)
        self.assertIs(type(lazy_box.mass()), evalcache.LazyObject)
        self.assertIs(type(lazy_box.faces()), evalcache.LazyObject)
        self.assertIs(type(lazy_box.unlazy()), Shape)

        zencad.lazy.onplace = True
        eager_box = zencad.box(2)

        self.assertIs(type(eager_box), Shape)
        self.assertIs(type(eager_box.mass()), float)
        self.assertIs(type(eager_box.faces()), list)
        self.assertTrue(all(type(face) is Shape for face in eager_box.faces()))

    def test_topology_sequence_and_index_are_generic_lazy_objects(self):
        faces = zencad.box(2).faces()
        first_face = faces[0]

        self.assertIs(type(faces), evalcache.LazyObject)
        self.assertIs(type(first_face), evalcache.LazyObject)
        self.assertIs(type(first_face.unlazy()), Shape)
        self.assertEqual(len(faces), 6)

    def test_unlazy_and_native_shape_accessor_materialize(self):
        lazy_box = zencad.box(2)

        self.assertIs(type(lazy_box.unlazy()), Shape)
        self.assertIsInstance(lazy_box.Shape(), TopoDS_Shape)

    def test_custom_lazy_extension_is_untyped_and_expands_tuples(self):
        @zencad.lazy
        def pair(left, right):
            return left, right

        proxy = pair(1, 2)
        self.assertIs(type(proxy), evalcache.LazyObject)
        self.assertEqual(evalcache.unlazy(proxy), [1, 2])

        zencad.lazy.onplace = True
        self.assertEqual(pair(1, 2), [1, 2])

    def test_curve_surface_types_are_hidden_by_generic_lazy_objects(self):
        cases = (
            (lambda: curve_circle(2), Curve),
            (lambda: curve2_ellipse(2, 1), Curve2),
            (lambda: cylinder_surface(2), Surface),
        )

        for factory, resolved_type in cases:
            with self.subTest(resolved_type=resolved_type.__name__):
                proxy = factory()
                self.assertIs(type(proxy), evalcache.LazyObject)
                self.assertIs(type(evalcache.unlazy(proxy)), resolved_type)

        zencad.lazy.onplace = True
        for factory, resolved_type in cases:
            with self.subTest(
                resolved_type=resolved_type.__name__,
                policy="onplace",
            ):
                self.assertIs(type(factory()), resolved_type)

    def test_historical_point_vector_result_type_mismatches(self):
        # Characterization only: these are known defects, not target algebra.
        vector = vector3(1, 2, 3)

        self.assertIs(type(vector + vector3(4, 5, 6)), point3)
        self.assertIs(type(vector * 2), point3)
        self.assertIs(
            type(point3(4, 5, 6) - point3(1, 1, 1)),
            vector3,
        )

    def test_historical_triangulate_face_proxy_mismatch(self):
        proxy = zencad.triangulate_face(zencad.rectangle(2, 2), 0.1)

        self.assertIs(type(proxy), LazyObjectShape)
        with self.assertRaisesRegex(
            Exception,
            "LazyObjectShape wraped type is not Shape",
        ):
            proxy.unlazy()

        # Bypassing LazyObjectShape's validator exposes evalcache.expand's
        # tuple-to-list conversion and the real structured result.
        result = evalcache.unlazy(proxy)
        self.assertIs(type(result), list)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(type(node) is point3 for node in result[0]))
        self.assertTrue(all(type(triangle) is list for triangle in result[1]))

    def test_cached_shape_graph_key_and_serialized_round_trip(self):
        zencad.lazy.encache = True
        zencad.lazy.decache = True
        zencad.lazy.fastdo = False

        first = zencad.box(12.345) - zencad.sphere(2.345)
        same = zencad.box(12.345) - zencad.sphere(2.345)
        different = zencad.box(12.345) - zencad.sphere(2.346)
        cache_key = first.__lazyhexhash__

        self.assertEqual(cache_key, same.__lazyhexhash__)
        self.assertNotEqual(cache_key, different.__lazyhexhash__)
        self.assertNotIn(cache_key, zencad.lazy.cache)

        first_value = first.unlazy()
        self.assertIs(type(first_value), Shape)
        self.assertIn(cache_key, zencad.lazy.cache)

        restored = zencad.box(12.345) - zencad.sphere(2.345)
        self.assertFalse(restored.__lazyheap__)
        restored_value = restored.unlazy()
        self.assertTrue(restored.__lazyheap__)
        self.assertIs(type(restored_value), Shape)
        self.assertAlmostEqual(restored_value.mass(), first_value.mass())

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
            brep_path = Path(temporary_directory) / "форма.brep"
            stl_path = Path(temporary_directory) / "форма.stl"

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

    def test_invalid_brep_has_actionable_error(self):
        with TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing.brep"
            with self.assertRaisesRegex(OSError, "Failed to read BREP"):
                _from_brep(str(missing))


if __name__ == "__main__":
    unittest.main()
