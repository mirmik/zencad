import math
import unittest

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.Geom import Geom_CartesianPoint
from OCP.TopoDS import TopoDS_Vertex
from OCP.gp import gp_Pnt, gp_Quaternion, gp_Vec
from evalcache.v2 import EvaluationMode, Expression

from zencad import _typed as typed


class TypedValueTransformCompatibilityTest(unittest.TestCase):
    def test_value_constructor_aliases_keep_stable_classes(self):
        observed = set()
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    runtime = typed.Runtime(mode=mode, cache=cache)
                    point = runtime.point3(1, 2)
                    vector = runtime.vector3((3, 4, 5))
                    quaternion = runtime.quat((0, 0, 0, 1))
                    observed.add((type(point), type(vector), type(quaternion)))
                    self.assertEqual(point.value(), (1.0, 2.0, 0.0))
                    self.assertEqual(vector.value(), (3.0, 4.0, 5.0))
                    self.assertEqual(quaternion.value(), (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(
            observed,
            {(typed.Point3, typed.Vector3, typed.Quaternion)},
        )

    def test_value_constructor_aliases_cover_legacy_inputs(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point3(1)

        self.assertEqual(runtime.point3().value(), (0.0, 0.0, 0.0))
        self.assertEqual(point.value(), (1.0, 0.0, 0.0))
        self.assertIs(runtime.point3(point), point)
        self.assertEqual(runtime.vector3(point).value(), point.value())
        self.assertEqual(runtime.point3([1, 2, 3]).value(), (1.0, 2.0, 3.0))
        self.assertEqual(runtime.point3(gp_Pnt(4, 5, 6)).value(), (4.0, 5.0, 6.0))
        self.assertEqual(runtime.vector3(gp_Vec(7, 8, 9)).value(), (7.0, 8.0, 9.0))
        vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(10, 11, 12)).Vertex()
        self.assertEqual(runtime.point3(vertex).value(), (10.0, 11.0, 12.0))
        self.assertEqual(
            runtime.quat(gp_Quaternion(0, 0, 0, 1)).value(),
            (0.0, 0.0, 0.0, 1.0),
        )

        with self.assertRaises(TypeError):
            runtime.point3(1, 2, 3, 4)
        with self.assertRaises(TypeError):
            runtime.quat((0, 0, 1))

    def test_legacy_value_spellings_preserve_typed_results(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point3(3, 4, 0)
        vector = runtime.vector3(0, 3, 4)

        self.assertEqual(point.to_tuple(), (3.0, 4.0, 0.0))
        self.assertEqual(point.to_array().tolist(), [3.0, 4.0, 0.0])
        self.assertIs(point.to_point3(), point)
        self.assertIs(vector.to_vector3(), vector)
        self.assertIs(type(point.to_vector3()), typed.Vector3)
        self.assertIs(type(vector.to_point3()), typed.Point3)
        self.assertIs(type(point.cross(vector)), typed.Vector3)
        self.assertIs(type(point.distance(runtime.point3(0, 0, 0))), typed.Scalar)
        self.assertIs(type(vector.angle(runtime.vector3(0, 0, 1))), typed.Scalar)
        self.assertIs(type(vector.normalize()), typed.Vector3)
        self.assertEqual(runtime.vector3().normalize().value(), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(float(point.length()), 5.0)
        self.assertTrue(point.early(runtime.point3(3, 4, 1e-6)))
        self.assertIsInstance(point.Pnt(), gp_Pnt)
        self.assertIsInstance(vector.Vec(), gp_Vec)
        self.assertFalse(point.Vtx().IsNull())

    def test_bulk_value_and_native_conversion_helpers(self):
        runtime = typed.Runtime.deferred(cache=False)
        points = runtime.points(((1, 2), gp_Pnt(3, 4, 5)))
        nested = runtime.points2((((1, 2, 3),), ((4, 5, 6),)))
        vectors = runtime.vectors(((7, 8, 9), points[0]))

        self.assertEqual(
            [point.value() for point in points], [(1.0, 2.0, 0.0), (3.0, 4.0, 5.0)]
        )
        self.assertEqual(nested[1][0].value(), (4.0, 5.0, 6.0))
        self.assertEqual(vectors[1].value(), (1.0, 2.0, 0.0))
        self.assertIsInstance(runtime.to_Vertex((1, 2, 3)), TopoDS_Vertex)
        self.assertIsInstance(runtime.to_GeomPoint(points[0]), Geom_CartesianPoint)

        self.assertLess(runtime.point3(1, 2, 3), runtime.vector3(1, 2, 4))
        point = runtime.point3(1, 2, 3)
        point += runtime.vector3(1, 1, 1)
        self.assertIs(type(point), typed.Point3)
        self.assertEqual(point.value(), (2.0, 3.0, 4.0))
        vector = runtime.vector3(3, 4, 5)
        vector -= runtime.vector3(1, 1, 1)
        self.assertIs(type(vector), typed.Vector3)
        self.assertEqual(vector.value(), (2.0, 3.0, 4.0))

    def test_runtime_transform_aliases_match_legacy_geometry(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point3(1, 2, 3)

        translations = (
            runtime.move(4, 5, 6),
            runtime.translate((4, 5, 6)),
            runtime.moveX(4) * runtime.moveY(5) * runtime.moveZ(6),
            runtime.right(4) * runtime.forw(5) * runtime.up(6),
        )
        for transform in translations:
            self.assertEqual(transform(point).value(), (5.0, 7.0, 9.0))

        self.assertEqual(runtime.left(4)(point).value(), (-3.0, 2.0, 3.0))
        self.assertEqual(runtime.back(2)(point).value(), (1.0, 0.0, 3.0))
        self.assertEqual(runtime.down(3)(point).value(), (1.0, 2.0, 0.0))
        self.assertEqual(runtime.nulltrans()(point), point)

        rotated = runtime.rotateZ(math.pi / 2)(runtime.point3(1, 0, 0)).value()
        self.assertAlmostEqual(rotated[0], 0.0, places=12)
        self.assertAlmostEqual(rotated[1], 1.0, places=12)
        rotation_vector = runtime.rotate(runtime.vector3(0, 0, math.pi / 2))
        self.assertEqual(
            rotation_vector(runtime.point3(1, 0, 0)),
            runtime.rotateZ(math.pi / 2)(runtime.point3(1, 0, 0)),
        )

        self.assertEqual(runtime.mirrorXY()(point).value(), (1.0, 2.0, -3.0))
        for actual, expected in zip(
            runtime.mirrorX()(point).value(), (1.0, -2.0, -3.0)
        ):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertEqual(runtime.mirrorO()(point).value(), (-1.0, -2.0, -3.0))

    def test_shape_transform_aliases_preserve_subtype_and_graph(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        size = runtime.box(2).mass() / 8
        shape = (
            runtime.box(size)
            .right(size)
            .forw(size)
            .up(size)
            .rotateZ(size)
            .scale(size, (0, 0, 0))
            .mirrorXY()
        )

        self.assertIs(type(shape), typed.Solid)
        self.assertIsInstance(shape._state, Expression)
        self.assertEqual(events, [])
        self.assertFalse(shape.native().IsNull())
        self.assertTrue(events)

    def test_transform_compatibility_methods_are_typed(self):
        runtime = typed.Runtime.deferred(cache=False)
        transform = runtime.move(1, 2, 3) * runtime.rotateX(math.pi / 4)
        point = runtime.point3(4, 5, 6)
        vector = runtime.vector3(4, 5, 6)

        moved_point = transform.transform_point(point)
        moved_vector = transform.transform_vector(vector)
        self.assertIs(type(moved_point), typed.Point3)
        self.assertIs(type(moved_vector), typed.Vector3)
        for actual, expected in zip(
            transform.inverse_transform_point(moved_point).value(), point.value()
        ):
            self.assertAlmostEqual(actual, expected, places=12)
        for actual, expected in zip(
            transform.inverse_transform_vector(moved_vector).value(), vector.value()
        ):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertIs(type(transform.rotation_quat()), typed.Quaternion)
        rotation_vector = transform.rotation_euler().value()
        self.assertAlmostEqual(rotation_vector[0], math.pi / 4, places=12)
        self.assertAlmostEqual(rotation_vector[1], 0.0, places=12)
        self.assertAlmostEqual(rotation_vector[2], 0.0, places=12)
        axis, angle = transform.rotation_axis_angle()
        self.assertEqual(axis.value(), (1.0, 0.0, 0.0))
        self.assertAlmostEqual(float(angle), math.pi / 4, places=12)
        self.assertTrue(str(transform).startswith("Transform(matrix="))
        self.assertEqual(str(runtime.quat((0, 0, 0, 1))), "quat(0.0,0.0,0.0,1.0)")

    def test_multi_transform_helpers_keep_typed_members(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        solid = runtime.box(1)
        transforms = runtime.rotate_array(4, array=True)

        self.assertIs(type(transforms), typed.MultiTransform)
        self.assertEqual(len(transforms), 4)
        items = transforms(solid)
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 4)
        self.assertTrue(all(type(item) is typed.Solid for item in items))
        self.assertTrue(all(isinstance(item._state, Expression) for item in items))
        self.assertEqual(events, [])

        fused = runtime.sqrmirror()(solid)
        self.assertIs(type(fused), typed.Shape)
        self.assertFalse(fused.native().IsNull())
        self.assertTrue(events)

        radial = runtime.rotate_array2(2, 3, endpoint=True, array=True)(solid)
        self.assertIsInstance(radial, list)
        self.assertEqual(len(radial), 2)

    def test_short_rotate_handles_parallel_and_opposite_vectors(self):
        runtime = typed.Runtime.deferred(cache=False)
        source = runtime.vector3(1, 0, 0)

        self.assertEqual(runtime.short_rotate(source, source), runtime.nulltrans())
        for target in (runtime.vector3(0, 1, 0), runtime.vector3(-1, 0, 0)):
            rotated = runtime.short_rotate(source, target)(source).normalized().value()
            expected = target.normalized().value()
            for actual, wanted in zip(rotated, expected):
                self.assertAlmostEqual(actual, wanted, places=12)

        with self.assertRaisesRegex(ValueError, "cannot be zero-length"):
            runtime.short_rotate(runtime.vector3(), source).matrix()

    def test_compatibility_helpers_reject_foreign_runtimes(self):
        first = typed.Runtime.deferred(cache=False)
        second = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            first.point3(second.point3(1, 2, 3))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            first.move(second.vector3(1, 2, 3))


if __name__ == "__main__":
    unittest.main()
