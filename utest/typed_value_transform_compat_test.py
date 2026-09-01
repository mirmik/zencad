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
                    context = typed.Context(mode=mode, cache=cache)
                    point = context.call(typed.point3, 1, 2)
                    vector = context.call(typed.vector3, (3, 4, 5))
                    quaternion = context.call(typed.quaternion, 0, 0, 0, 1)
                    observed.add((type(point), type(vector), type(quaternion)))
                    self.assertEqual(point.value(), (1.0, 2.0, 0.0))
                    self.assertEqual(vector.value(), (3.0, 4.0, 5.0))
                    self.assertEqual(quaternion.value(), (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(
            observed,
            {(typed.Point3, typed.Vector3, typed.Quaternion)},
        )

    def test_value_constructor_aliases_cover_legacy_inputs(self):
        context = typed.Context.deferred(cache=False)
        point = context.call(typed.point3, 1)

        self.assertEqual(context.call(typed.point3, ).value(), (0.0, 0.0, 0.0))
        self.assertEqual(point.value(), (1.0, 0.0, 0.0))
        self.assertIs(context.call(typed.point3, point), point)
        self.assertEqual(context.call(typed.vector3, point).value(), point.value())
        self.assertEqual(context.call(typed.point3, [1, 2, 3]).value(), (1.0, 2.0, 3.0))
        self.assertEqual(context.call(typed.point3, gp_Pnt(4, 5, 6)).value(), (4.0, 5.0, 6.0))
        self.assertEqual(context.call(typed.vector3, gp_Vec(7, 8, 9)).value(), (7.0, 8.0, 9.0))
        vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(10, 11, 12)).Vertex()
        self.assertEqual(context.call(typed.point3, vertex).value(), (10.0, 11.0, 12.0))
        self.assertEqual(
            typed.Quaternion.from_ocp(
                gp_Quaternion(0, 0, 0, 1),
                context=context,
            ).value(),
            (0.0, 0.0, 0.0, 1.0),
        )

        with self.assertRaises(TypeError):
            context.call(typed.point3, 1, 2, 3, 4)
        with self.assertRaises(TypeError):
            context.call(typed.quaternion, 0, 0, 1)  # type: ignore[call-arg]

    def test_legacy_value_spellings_preserve_typed_results(self):
        context = typed.Context.deferred(cache=False)
        point = context.call(typed.point3, 3, 4, 0)
        vector = context.call(typed.vector3, 0, 3, 4)

        self.assertEqual(point.to_tuple(), (3.0, 4.0, 0.0))
        self.assertEqual(point.to_array().tolist(), [3.0, 4.0, 0.0])
        self.assertIs(point.to_point3(), point)
        self.assertIs(vector.to_vector3(), vector)
        self.assertIs(type(point.to_vector3()), typed.Vector3)
        self.assertIs(type(vector.to_point3()), typed.Point3)
        self.assertIs(type(point.cross(vector)), typed.Vector3)
        self.assertIs(type(point.distance(context.call(typed.point3, 0, 0, 0))), typed.Scalar)
        self.assertIs(type(vector.angle(context.call(typed.vector3, 0, 0, 1))), typed.Scalar)
        self.assertIs(type(vector.normalize()), typed.Vector3)
        self.assertEqual(context.call(typed.vector3, ).normalize().value(), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(float(point.length()), 5.0)
        self.assertTrue(point.early(context.call(typed.point3, 3, 4, 1e-6)))
        self.assertIsInstance(point.Pnt(), gp_Pnt)
        self.assertIsInstance(vector.Vec(), gp_Vec)
        self.assertFalse(point.Vtx().IsNull())

    def test_bulk_value_and_native_conversion_helpers(self):
        context = typed.Context.deferred(cache=False)
        points = tuple(
            context.call(typed.point3, value)
            for value in ((1, 2), gp_Pnt(3, 4, 5))
        )
        nested = tuple(
            tuple(context.call(typed.point3, value) for value in row)
            for row in (((1, 2, 3),), ((4, 5, 6),))
        )
        vectors = tuple(
            context.call(typed.vector3, value)
            for value in ((7, 8, 9), points[0])
        )

        self.assertEqual(
            [point.value() for point in points], [(1.0, 2.0, 0.0), (3.0, 4.0, 5.0)]
        )
        self.assertEqual(nested[1][0].value(), (4.0, 5.0, 6.0))
        self.assertEqual(vectors[1].value(), (1.0, 2.0, 0.0))
        self.assertIsInstance(context.call(typed.point3, 1, 2, 3).Vtx(), TopoDS_Vertex)
        self.assertIsInstance(Geom_CartesianPoint(points[0].Pnt()), Geom_CartesianPoint)

        self.assertLess(context.call(typed.point3, 1, 2, 3), context.call(typed.vector3, 1, 2, 4))
        point = context.call(typed.point3, 1, 2, 3)
        point += context.call(typed.vector3, 1, 1, 1)
        self.assertIs(type(point), typed.Point3)
        self.assertEqual(point.value(), (2.0, 3.0, 4.0))
        vector = context.call(typed.vector3, 3, 4, 5)
        vector -= context.call(typed.vector3, 1, 1, 1)
        self.assertIs(type(vector), typed.Vector3)
        self.assertEqual(vector.value(), (2.0, 3.0, 4.0))

    def test_context_transform_aliases_match_legacy_geometry(self):
        context = typed.Context.deferred(cache=False)
        point = context.call(typed.point3, 1, 2, 3)

        translations = (
            context.call(typed.move, 4, 5, 6),
            context.call(typed.translate, (4, 5, 6)),
            context.call(typed.moveX, 4) * context.call(typed.moveY, 5) * context.call(typed.moveZ, 6),
            context.call(typed.right, 4) * context.call(typed.forw, 5) * context.call(typed.up, 6),
        )
        for transform in translations:
            self.assertEqual(transform(point).value(), (5.0, 7.0, 9.0))

        self.assertEqual(context.call(typed.left, 4)(point).value(), (-3.0, 2.0, 3.0))
        self.assertEqual(context.call(typed.back, 2)(point).value(), (1.0, 0.0, 3.0))
        self.assertEqual(context.call(typed.down, 3)(point).value(), (1.0, 2.0, 0.0))
        self.assertEqual(context.call(typed.nulltrans, )(point), point)

        rotated = context.call(typed.rotateZ, math.pi / 2)(context.call(typed.point3, 1, 0, 0)).value()
        self.assertAlmostEqual(rotated[0], 0.0, places=12)
        self.assertAlmostEqual(rotated[1], 1.0, places=12)
        rotation_vector = context.call(typed.rotate, context.call(typed.vector3, 0, 0, math.pi / 2))
        self.assertEqual(
            rotation_vector(context.call(typed.point3, 1, 0, 0)),
            context.call(typed.rotateZ, math.pi / 2)(context.call(typed.point3, 1, 0, 0)),
        )

        self.assertEqual(context.call(typed.mirrorXY, )(point).value(), (1.0, 2.0, -3.0))
        for actual, expected in zip(
            context.call(typed.mirrorX, )(point).value(), (1.0, -2.0, -3.0)
        ):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertEqual(context.call(typed.mirrorO, )(point).value(), (-1.0, -2.0, -3.0))

    def test_shape_transform_aliases_preserve_subtype_and_graph(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        size = context.call(typed.box, 2).mass() / 8
        shape = (
            context.call(typed.box, size)
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
        context = typed.Context.deferred(cache=False)
        transform = context.call(typed.move, 1, 2, 3) * context.call(typed.rotateX, math.pi / 4)
        point = context.call(typed.point3, 4, 5, 6)
        vector = context.call(typed.vector3, 4, 5, 6)

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
        self.assertEqual(
            context.call(typed.quaternion, 0, 0, 0, 1).value(),
            (0.0, 0.0, 0.0, 1.0),
        )

    def test_multi_transform_helpers_keep_typed_members(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        solid = context.call(typed.box, 1)
        transforms = typed.MultiTransform(
            tuple(context.call(typed.rotateZ, index * math.pi / 2) for index in range(4)),
            context=context,
            array=True,
        )

        self.assertIs(type(transforms), typed.MultiTransform)
        self.assertEqual(len(transforms), 4)
        items = transforms(solid)
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 4)
        self.assertTrue(all(type(item) is typed.Solid for item in items))
        self.assertTrue(all(isinstance(item._state, Expression) for item in items))
        self.assertEqual(events, [])

        mirrors = typed.MultiTransform(
            (
                context.call(typed.identity_transform),
                context.call(typed.mirrorYZ),
                context.call(typed.mirrorXZ),
                context.call(typed.mirrorZ),
            ),
            context=context,
        )
        fused = mirrors(solid)
        self.assertIs(type(fused), typed.Shape)
        self.assertFalse(fused.native().IsNull())
        self.assertTrue(events)

        radial = typed.MultiTransform(
            (
                context.call(typed.rotateX, math.pi / 2),
                context.call(typed.rotateZ, math.pi)
                * context.call(typed.right, 3)
                * context.call(typed.rotateX, math.pi / 2),
            ),
            context=context,
            array=True,
        )(solid)
        self.assertIsInstance(radial, list)
        self.assertEqual(len(radial), 2)

    def test_short_rotate_handles_parallel_and_opposite_vectors(self):
        context = typed.Context.deferred(cache=False)
        source = context.call(typed.vector3, 1, 0, 0)

        self.assertEqual(context.call(typed.short_rotate, source, source), context.call(typed.nulltrans, ))
        for target in (context.call(typed.vector3, 0, 1, 0), context.call(typed.vector3, -1, 0, 0)):
            rotated = context.call(typed.short_rotate, source, target)(source).normalized().value()
            expected = target.normalized().value()
            for actual, wanted in zip(rotated, expected):
                self.assertAlmostEqual(actual, wanted, places=12)

        with self.assertRaisesRegex(ValueError, "cannot be zero-length"):
            context.call(typed.short_rotate, context.call(typed.vector3, ), source).matrix()

    def test_compatibility_helpers_reject_foreign_contexts(self):
        first = typed.Context.deferred(cache=False)
        second = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different contexts"):
            first.call(typed.point3, second.call(typed.point3, 1, 2, 3))
        with self.assertRaisesRegex(ValueError, "different contexts"):
            first.call(typed.move, second.call(typed.vector3, 1, 2, 3))


if __name__ == "__main__":
    unittest.main()
