import math
import unittest

import numpy
from OCP.gp import gp_Pnt, gp_Pnt2d, gp_Vec, gp_Vec2d
from evalcache.v2 import CacheRecord, EvaluationMode, Expression

from zencad import _typed as typed


class CountingStore:
    def __init__(self):
        self.records: dict[str, CacheRecord] = {}
        self.reads = 0
        self.writes = 0
        self.deletes = 0

    def get(self, key: str):
        self.reads += 1
        return self.records.get(key)

    def put(self, key: str, record: CacheRecord):
        self.writes += 1
        self.records[key] = record

    def delete(self, key: str):
        self.deletes += 1
        self.records.pop(key, None)

    @property
    def accesses(self):
        return self.reads + self.writes + self.deletes


class TypedValueAlgebraTest(unittest.TestCase):
    def test_result_classes_are_stable_in_all_policy_combinations(self):
        observed = set()
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    runtime = typed.Runtime(mode=mode, cache=cache)
                    scalar = runtime.scalar(2)
                    point2 = runtime.point2(1, 2)
                    vector2 = runtime.vector2(3, 4)
                    point3 = runtime.point(1, 2, 3)
                    vector3 = runtime.vector(4, 5, 6)
                    results = (
                        scalar + 1,
                        point2 + vector2,
                        point2 - point2,
                        vector2 + vector2,
                        point3 + vector3,
                        point3 - point3,
                        vector3 + vector3,
                        vector3.cross(runtime.vector(0, 1, 0)),
                    )
                    observed.add(tuple(type(value) for value in results))
        self.assertEqual(len(observed), 1)

    def test_scalar_algebra_and_python_boundaries(self):
        runtime = typed.Runtime.deferred(cache=False)
        scalar = runtime.scalar(5)

        table = (
            (scalar + 2, 7.0),
            (2 + scalar, 7.0),
            (scalar - 2, 3.0),
            (8 - scalar, 3.0),
            (scalar * 2, 10.0),
            (2 * scalar, 10.0),
            (scalar / 2, 2.5),
            (10 / scalar, 2.0),
            (scalar // 2, 2.0),
            (12 % scalar, 2.0),
            (scalar**2, 25.0),
            (2 ** runtime.scalar(3), 8.0),
            (-scalar, -5.0),
            (abs(-scalar), 5.0),
        )
        for result, expected in table:
            with self.subTest(expected=expected):
                self.assertIs(type(result), typed.Scalar)
                self.assertEqual(float(result), expected)

        self.assertEqual(int(runtime.scalar(3.9)), 3)
        self.assertTrue(runtime.scalar(1))
        self.assertFalse(runtime.scalar(0))
        self.assertTrue(scalar > 4)
        self.assertTrue(scalar >= 5)
        self.assertTrue(scalar < 6)
        self.assertTrue(scalar <= 5)
        self.assertTrue(scalar == 5)

    def test_3d_algebra_has_geometrically_correct_result_types(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point(10, 20, 30)
        other_point = typed.Point3((4, 5, 6), runtime=runtime)
        vector = runtime.vector(1, 2, 3)
        other_vector = typed.Vector3((4, 5, 6), runtime=runtime)

        cases = (
            (vector + other_vector, typed.Vector3, (5.0, 7.0, 9.0)),
            (vector - other_vector, typed.Vector3, (-3.0, -3.0, -3.0)),
            (point + vector, typed.Point3, (11.0, 22.0, 33.0)),
            (vector + point, typed.Point3, (11.0, 22.0, 33.0)),
            (point - vector, typed.Point3, (9.0, 18.0, 27.0)),
            (point - other_point, typed.Vector3, (6.0, 15.0, 24.0)),
            (vector * 2, typed.Vector3, (2.0, 4.0, 6.0)),
            (runtime.scalar(2) * vector, typed.Vector3, (2.0, 4.0, 6.0)),
            (vector / 2, typed.Vector3, (0.5, 1.0, 1.5)),
            (-vector, typed.Vector3, (-1.0, -2.0, -3.0)),
            (vector.cross(other_vector), typed.Vector3, (-3.0, 6.0, -3.0)),
        )
        for result, expected_type, expected_value in cases:
            with self.subTest(expected_type=expected_type.__name__):
                self.assertIs(type(result), expected_type)
                self.assertEqual(result.value(), expected_value)

        self.assertEqual(vector.dot(other_vector).value(), 32.0)
        self.assertAlmostEqual(vector.length().value(), math.sqrt(14))
        self.assertAlmostEqual(point.distance_to(other_point).value(), math.sqrt(837))
        normalized = vector.normalized().value()
        self.assertAlmostEqual(sum(value * value for value in normalized), 1.0)

    def test_2d_algebra_has_geometrically_correct_result_types(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = typed.Point2((10, 20), runtime=runtime)
        other_point = runtime.point2(4, 5)
        vector = typed.Vector2((1, 2), runtime=runtime)
        other_vector = runtime.vector2(4, 5)

        cases = (
            (vector + other_vector, typed.Vector2, (5.0, 7.0)),
            (point + vector, typed.Point2, (11.0, 22.0)),
            (vector + point, typed.Point2, (11.0, 22.0)),
            (point - vector, typed.Point2, (9.0, 18.0)),
            (point - other_point, typed.Vector2, (6.0, 15.0)),
            (vector * 3, typed.Vector2, (3.0, 6.0)),
        )
        for result, expected_type, expected_value in cases:
            self.assertIs(type(result), expected_type)
            self.assertEqual(result.value(), expected_value)

        self.assertEqual(vector.dot(other_vector).value(), 14.0)
        self.assertEqual(vector.cross(other_vector).value(), -3.0)
        self.assertEqual(point.distance_to(other_point).value(), math.sqrt(261))

    def test_vector_and_point_algebra_laws(self):
        runtime = typed.Runtime.deferred(cache=False)
        vector = runtime.vector(1, -2, 3)
        other_vector = runtime.vector(4, 5, -6)
        point = runtime.point(7, 8, 9)
        other_point = runtime.point(-1, 2, 4)

        self.assertEqual((vector + other_vector) - other_vector, vector)
        self.assertEqual(point + (other_point - point), other_point)
        self.assertEqual(vector.dot(other_vector), other_vector.dot(vector))
        self.assertEqual(vector.cross(other_vector), -other_vector.cross(vector))
        self.assertEqual((vector + other_vector) * 3, vector * 3 + other_vector * 3)

    def test_literal_value_graphs_constant_fold_without_evaluator_or_cache(self):
        events = []
        store = CountingStore()
        runtime = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )

        result = (
            runtime.point(1, 2, 3)
            + (runtime.vector(2, 4, 6) / runtime.scalar(2)).normalized()
        ).distance_to(runtime.point(0, 0, 0))
        result = typed.sqrt(result**2)

        self.assertIs(type(result), typed.Scalar)
        self.assertNotIsInstance(result._state, Expression)
        self.assertEqual(events, [])
        self.assertEqual(store.accesses, 0)
        self.assertGreater(float(result), 0)
        self.assertEqual(events, [])
        self.assertEqual(store.accesses, 0)

    def test_deferred_geometry_dependencies_are_not_folded_or_materialized(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        mass = runtime.box(2).mass()
        result = typed.sqrt((mass + 1) * 2)

        self.assertIs(type(result), typed.Scalar)
        self.assertIsInstance(result._state, Expression)
        self.assertEqual(events, [])

        self.assertGreater(float(result), 0)
        operation_ids = [event.operation_id for event in events]
        self.assertIn("zencad.typed.math.sqrt", operation_ids)
        self.assertIn("zencad.typed.scalar.add", operation_ids)
        self.assertIn("zencad.typed.shape.mass", operation_ids)

    def test_immediate_geometry_value_then_uses_constant_folding(self):
        events = []
        runtime = typed.Runtime.immediate(
            cache=False,
            progress_hooks=(events.append,),
        )
        mass = runtime.box(2).mass()
        before = len(events)
        result = typed.sqrt(mass + 1)

        self.assertNotIsInstance(result._state, Expression)
        self.assertEqual(len(events), before)
        self.assertNotIn(
            "zencad.typed.scalar.add",
            [event.operation_id for event in events],
        )

    def test_comparison_truth_and_foreign_math_materialize(self):
        for boundary in (
            lambda value: value > 0,
            bool,
            float,
            math.sin,
        ):
            with self.subTest(boundary=getattr(boundary, "__name__", "comparison")):
                events = []
                runtime = typed.Runtime.deferred(
                    cache=False,
                    progress_hooks=(events.append,),
                )
                value = runtime.box(2).mass()
                self.assertEqual(events, [])
                boundary(value)
                self.assertTrue(events)

    def test_numpy_iteration_and_ocp_are_explicit_boundaries(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        center = runtime.box(2).center()
        self.assertEqual(events, [])

        array = center.to_numpy()
        self.assertIs(type(array), numpy.ndarray)
        numpy.testing.assert_allclose(array, (1, 1, 1))
        self.assertTrue(events)
        self.assertIsInstance(center.to_ocp(), gp_Pnt)
        self.assertEqual(tuple(center), (1.0, 1.0, 1.0))

        self.assertIsInstance(runtime.vector(1, 2, 3).to_ocp(), gp_Vec)
        self.assertIsInstance(runtime.point2(1, 2).to_ocp(), gp_Pnt2d)
        self.assertIsInstance(runtime.vector2(1, 2).to_ocp(), gp_Vec2d)

    def test_expression_aware_math_helpers_preserve_scalar(self):
        runtime = typed.Runtime.deferred(cache=False)
        value = runtime.scalar(0.5)
        helpers = (
            typed.sin,
            typed.cos,
            typed.tan,
            typed.asin,
            typed.acos,
            typed.atan,
            typed.sqrt,
            typed.exp,
            typed.log,
        )
        positive = runtime.scalar(0.5)
        for helper in helpers:
            argument = positive
            result = helper(argument)
            self.assertIs(type(result), typed.Scalar)
        self.assertIs(type(typed.atan2(value, 2)), typed.Scalar)
        self.assertIs(type(typed.atan2(2, value)), typed.Scalar)

    def test_invalid_algebra_and_mutability_escape_hatches_are_rejected(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point(1, 2, 3)
        vector = runtime.vector(1, 2, 3)

        with self.assertRaises(TypeError):
            _ = point + point
        with self.assertRaises(TypeError):
            _ = point + runtime.vector2(1, 2)
        with self.assertRaises(ValueError):
            runtime.vector(0, 0, 0).normalized()
        with self.assertRaises(TypeError):
            hash(vector)
        with self.assertRaises(TypeError):
            typed.Point3(1, 2, 3)
        with self.assertRaises(TypeError):
            runtime.scalar(True)

        self.assertNotIsInstance(vector, float)
        self.assertNotIsInstance(vector, numpy.ndarray)
        self.assertNotIsInstance(vector, Expression)


if __name__ == "__main__":
    unittest.main()
