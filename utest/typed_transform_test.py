import math
import random
import sys
import unittest

from OCP.gp import gp_Pnt, gp_Quaternion, gp_Trsf, gp_Vec
from evalcache.v2 import CacheRecord, EvaluationMode, Expression

from zencad import _typed as typed


TOLERANCE = 1e-12


class SpyStore:
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


class TypedTransformTest(unittest.TestCase):
    def assertCoordinatesAlmostEqual(
        self,
        actual,
        expected,
        *,
        tolerance=TOLERANCE,
    ):
        self.assertEqual(len(actual), len(expected))
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            self.assertAlmostEqual(
                actual_item,
                expected_item,
                delta=tolerance,
                msg=f"coordinate {index}: {actual!r} != {expected!r}",
            )

    def assertMatricesAlmostEqual(
        self,
        actual,
        expected,
        *,
        tolerance=TOLERANCE,
    ):
        self.assertEqual(len(actual), len(expected))
        for row, expected_row in zip(actual, expected):
            self.assertCoordinatesAlmostEqual(
                row,
                expected_row,
                tolerance=tolerance,
            )

    def test_result_classes_are_stable_in_all_policy_combinations(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    store = SpyStore()
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=store,
                        progress_hooks=(events.append,),
                    )
                    shape = runtime.box(1, 2, 3)
                    mass = shape.mass()
                    center = shape.center()
                    axis = typed.Vector3(center.x, center.y, center.z)
                    quaternion = runtime.quaternion_axis_angle(axis, mass / 10)
                    offset = typed.Vector3(center.x, center.y, center.z)
                    transform = (
                        runtime.translation(offset)
                        * runtime.rotation(quaternion)
                        * runtime.scale(mass / 3, center=center)
                    )
                    point = transform(center)
                    vector = transform(axis)
                    moved = shape.transform(transform)

                    result_types = tuple(
                        type(value)
                        for value in (
                            quaternion,
                            transform,
                            transform.scale,
                            transform.rotation,
                            transform.translation,
                            point,
                            vector,
                            moved,
                        )
                    )
                    observed_types.add(result_types)
                    self.assertEqual(
                        result_types,
                        (
                            typed.Quaternion,
                            typed.Transform,
                            typed.Scalar,
                            typed.Quaternion,
                            typed.Vector3,
                            typed.Point3,
                            typed.Vector3,
                            typed.Solid,
                        ),
                    )

                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])
                        self.assertEqual(store.accesses, 0)
                        for value in (quaternion, transform, point, vector, moved):
                            self.assertIsInstance(value._state, Expression)

                    self.assertFalse(moved.native().IsNull())
                    if cache:
                        self.assertGreater(store.reads, 0)
                        self.assertGreater(store.writes, 0)
                    else:
                        self.assertEqual(store.accesses, 0)

        self.assertEqual(len(observed_types), 1)

    def test_literal_operations_fold_without_evaluator_events_or_cache(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            with self.subTest(mode=mode):
                events = []
                store = SpyStore()
                runtime = typed.Runtime(
                    mode=mode,
                    cache=True,
                    cache_store=store,
                    progress_hooks=(events.append,),
                )
                first = runtime.quaternion(0, 0, 2, 2)
                second = runtime.quaternion_axis_angle(
                    runtime.vector(0, 1, 0), math.pi / 3
                )
                quaternion = (first * second).inverse()
                transform = (
                    runtime.translation(1, 2, 3)
                    * runtime.rotation(quaternion)
                    * runtime.scale(
                        -2,
                        center=runtime.point(3, 2, 1),
                    )
                    * runtime.mirror(
                        runtime.vector(0, 0, 1),
                        origin=runtime.point(0, 0, 2),
                    )
                )
                point = transform(runtime.point(4, 5, 6))
                vector = transform(runtime.vector(4, 5, 6))
                values = (
                    first,
                    second,
                    quaternion,
                    transform,
                    transform.inverse(),
                    transform.scale,
                    transform.rotation,
                    transform.translation,
                    point,
                    vector,
                    quaternion.x,
                    quaternion.y,
                    quaternion.z,
                    quaternion.w,
                )

                for value in values:
                    self.assertNotIsInstance(value._state, Expression)

                quaternion.value()
                transform.matrix()
                point.value()
                vector.value()
                self.assertEqual(events, [])
                self.assertEqual(store.accesses, 0)

    def test_shape_derived_operands_preserve_the_complete_graph(self):
        events = []
        store = SpyStore()
        runtime = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        shape = runtime.box(2)
        mass = shape.mass()
        center = shape.center()
        axis = typed.Vector3(center.x, center.y, center.z)
        angle = mass / 16
        offset = typed.Vector3(center.x, mass / 8, center.z)
        quaternion = runtime.quaternion_axis_angle(axis, angle)
        norm = quaternion.norm()
        translation = runtime.translation(offset)
        rotation = runtime.rotation(quaternion)
        scale = runtime.scale((mass / 4) * norm, center=center)
        transform = translation * rotation * scale
        point = transform(runtime.point(1, 2, 3))
        moved = shape.transform(transform)

        for value in (
            mass,
            center,
            axis,
            angle,
            offset,
            quaternion,
            norm,
            translation,
            rotation,
            scale,
            transform,
            point,
            moved,
        ):
            self.assertIsInstance(value._state, Expression)
        self.assertEqual(events, [])
        self.assertEqual(store.accesses, 0)

        self.assertFalse(moved.native().IsNull())
        operation_ids = {event.operation_id for event in events}
        self.assertTrue(
            {
                "zencad.typed.shape.mass",
                "zencad.typed.shape.center",
                "zencad.typed.quaternion.axis_angle",
                "zencad.typed.quaternion.norm",
                "zencad.typed.transform.translation",
                "zencad.typed.transform.rotation",
                "zencad.typed.transform.scale",
                "zencad.typed.transform.compose",
                "zencad.typed.shape.transform",
            }.issubset(operation_ids)
        )
        self.assertGreater(store.reads, 0)
        self.assertGreater(store.writes, 0)

    def test_transform_composition_order_and_then_are_unambiguous(self):
        runtime = typed.Runtime.deferred(cache=False)
        point = runtime.point(1, 0, 0)
        move = runtime.translation(1, 0, 0)
        rotate = runtime.rotation(
            runtime.vector(0, 0, 1),
            math.pi / 2,
        )

        # outer * inner applies inner first.
        self.assertCoordinatesAlmostEqual(
            (rotate * move)(point).value(),
            (0.0, 2.0, 0.0),
        )
        self.assertCoordinatesAlmostEqual(
            (move * rotate)(point).value(),
            (1.0, 1.0, 0.0),
        )
        # then reads in application order: move first, rotate second.
        self.assertCoordinatesAlmostEqual(
            move.then(rotate)(point).value(),
            (rotate * move)(point).value(),
        )

    def test_quaternion_composition_norm_and_sign_canonicalization(self):
        runtime = typed.Runtime.deferred(cache=False)
        x_rotation = runtime.quaternion_axis_angle(runtime.vector(1, 0, 0), math.pi / 2)
        y_rotation = runtime.quaternion_axis_angle(runtime.vector(0, 1, 0), math.pi / 3)
        vector = runtime.vector(2, -3, 4)

        composed = y_rotation * x_rotation
        self.assertCoordinatesAlmostEqual(
            composed.rotate(vector).value(),
            y_rotation.rotate(x_rotation.rotate(vector)).value(),
        )
        self.assertCoordinatesAlmostEqual(
            x_rotation.then(y_rotation).rotate(vector).value(),
            composed.rotate(vector).value(),
        )
        self.assertAlmostEqual(float(composed.norm()), 1.0, delta=TOLERANCE)
        self.assertAlmostEqual(
            sum(component * component for component in composed.value()),
            1.0,
            delta=TOLERANCE,
        )
        self.assertIs(composed.normalized(), composed)
        self.assertEqual(composed.conjugate(), composed.inverse())

        positive = runtime.quaternion(1, 2, 3, 4)
        negative = runtime.quaternion(-1, -2, -3, -4)
        self.assertEqual(positive, negative)
        self.assertEqual(positive.value(), negative.value())
        self.assertEqual(
            runtime.quaternion(-1, 0, 0, 0).value(),
            (1.0, 0.0, 0.0, 0.0),
        )

        subnormal_axis = runtime.quaternion_axis_angle(
            runtime.vector(5e-324, 0, 0), math.pi / 2
        )
        self.assertCoordinatesAlmostEqual(
            subnormal_axis.rotate(runtime.vector(0, 1, 0)).value(),
            (0.0, 0.0, 1.0),
        )

        identity = typed.Quaternion.identity(runtime=runtime)
        self.assertEqual((identity * positive).value(), positive.value())
        self.assertEqual((positive * identity).value(), positive.value())
        transform = runtime.translation(1, 2, 3) * positive.to_transform()
        identity_transform = runtime.identity_transform()
        self.assertEqual((identity_transform * transform).matrix(), transform.matrix())
        self.assertEqual((transform * identity_transform).matrix(), transform.matrix())

    def test_point_and_vector_application_have_distinct_translation_semantics(self):
        runtime = typed.Runtime.deferred(cache=False)
        transform = (
            runtime.translation(10, -2, 7)
            * runtime.rotation(runtime.vector(0, 0, 1), math.pi / 2)
            * runtime.scale(2)
        )
        point = runtime.point(1, 2, 3)
        vector = runtime.vector(1, 2, 3)

        transformed_point = transform.apply(point)
        transformed_vector = transform.apply(vector)
        self.assertIs(type(transformed_point), typed.Point3)
        self.assertIs(type(transformed_vector), typed.Vector3)
        self.assertCoordinatesAlmostEqual(
            transformed_point.value(),
            (6.0, 0.0, 13.0),
        )
        self.assertCoordinatesAlmostEqual(
            transformed_vector.value(),
            (-4.0, 2.0, 6.0),
        )
        self.assertEqual(
            runtime.translation(10, -2, 7)(vector),
            vector,
        )

    def test_transform_and_quaternion_inverses_round_trip(self):
        runtime = typed.Runtime.deferred(cache=False)
        quaternion = runtime.quaternion_axis_angle(runtime.vector(2, -1, 4), 1.234)
        transform = (
            runtime.translation(3, -5, 7)
            * runtime.rotation(quaternion)
            * runtime.scale(
                -1.25,
                center=runtime.point(2, 1, -3),
            )
        )
        point = runtime.point(-4, 8, 0.5)
        vector = runtime.vector(2, 3, -7)

        self.assertCoordinatesAlmostEqual(
            transform.inverse()(transform(point)).value(),
            point.value(),
        )
        self.assertCoordinatesAlmostEqual(
            transform.inverse()(transform(vector)).value(),
            vector.value(),
        )
        self.assertCoordinatesAlmostEqual(
            quaternion.inverse().rotate(quaternion.rotate(vector)).value(),
            vector.value(),
        )
        self.assertMatricesAlmostEqual(
            (transform * transform.inverse()).matrix(),
            runtime.identity_transform().matrix(),
        )

    def test_scale_about_center_supports_signed_scale(self):
        runtime = typed.Runtime.deferred(cache=False)
        center = runtime.point(1, 2, 3)
        scale = runtime.scale(-2, center=center)

        self.assertCoordinatesAlmostEqual(scale(center).value(), center.value())
        self.assertCoordinatesAlmostEqual(
            scale(runtime.point(2, 4, 6)).value(),
            (-1.0, -2.0, -3.0),
        )
        self.assertCoordinatesAlmostEqual(
            scale(runtime.vector(1, 2, 3)).value(),
            (-2.0, -4.0, -6.0),
        )
        self.assertEqual(float(scale.scale), -2.0)

    def test_mirror_plane_is_an_involution(self):
        runtime = typed.Runtime.deferred(cache=False)
        mirror = runtime.mirror(
            runtime.vector(0, 0, 2),
            origin=runtime.point(0, 0, 3),
        )
        point = runtime.point(1, 2, 5)
        vector = runtime.vector(1, 2, 3)

        self.assertCoordinatesAlmostEqual(
            mirror(point).value(),
            (1.0, 2.0, 1.0),
        )
        self.assertCoordinatesAlmostEqual(
            mirror(vector).value(),
            (1.0, 2.0, -3.0),
        )
        self.assertCoordinatesAlmostEqual(
            mirror(mirror(point)).value(),
            point.value(),
        )
        self.assertCoordinatesAlmostEqual(
            mirror(mirror(vector)).value(),
            vector.value(),
        )
        self.assertMatricesAlmostEqual(
            (mirror * mirror).matrix(),
            runtime.identity_transform().matrix(),
        )

    def test_ocp_round_trip_and_fresh_mutable_boundaries(self):
        runtime = typed.Runtime.deferred(cache=False)
        quaternion = runtime.quaternion_axis_angle(
            runtime.vector(1, -2, 3),
            0.75,
        )
        transform = (
            runtime.translation(4, 5, -6)
            * runtime.rotation(quaternion)
            * runtime.scale(-2)
        )

        ocp_quaternion = quaternion.to_ocp()
        self.assertIsInstance(ocp_quaternion, gp_Quaternion)
        restored_quaternion = typed.Quaternion.from_ocp(
            ocp_quaternion,
            runtime=runtime,
        )
        self.assertCoordinatesAlmostEqual(
            restored_quaternion.value(),
            quaternion.value(),
        )
        second_ocp_quaternion = quaternion.to_ocp()
        self.assertIsNot(ocp_quaternion, second_ocp_quaternion)
        ocp_quaternion.SetIdent()
        self.assertCoordinatesAlmostEqual(
            (
                second_ocp_quaternion.X(),
                second_ocp_quaternion.Y(),
                second_ocp_quaternion.Z(),
                second_ocp_quaternion.W(),
            ),
            quaternion.value(),
        )
        self.assertCoordinatesAlmostEqual(
            restored_quaternion.value(),
            quaternion.value(),
        )

        ocp_transform = transform.to_ocp()
        self.assertIsInstance(ocp_transform, gp_Trsf)
        restored_transform = typed.Transform.from_ocp(
            ocp_transform,
            runtime=runtime,
        )
        self.assertMatricesAlmostEqual(
            restored_transform.matrix(),
            transform.matrix(),
        )
        second_ocp_transform = transform.to_ocp()
        self.assertIsNot(ocp_transform, second_ocp_transform)
        ocp_transform.SetTranslationPart(gp_Vec(99, 98, 97))
        self.assertMatricesAlmostEqual(
            restored_transform.matrix(),
            transform.matrix(),
        )
        self.assertCoordinatesAlmostEqual(
            (
                second_ocp_transform.TranslationPart().X(),
                second_ocp_transform.TranslationPart().Y(),
                second_ocp_transform.TranslationPart().Z(),
            ),
            (4.0, 5.0, -6.0),
        )

        point = runtime.point(2, -1, 8)
        native_point = gp_Pnt(*point.value())
        native_point.Transform(transform.to_ocp())
        self.assertCoordinatesAlmostEqual(
            transform(point).value(),
            (native_point.X(), native_point.Y(), native_point.Z()),
        )

    def test_shape_transform_uses_the_typed_adapter(self):
        runtime = typed.Runtime.deferred(cache=False)
        shape = runtime.box(1, 2, 3)
        transform = runtime.translation(4, -2, 7) * runtime.rotation(
            runtime.vector(0, 0, 1), math.pi / 2
        )
        moved = shape.transform(transform)

        self.assertIs(type(moved), typed.Solid)
        self.assertFalse(moved.native().IsNull())
        self.assertAlmostEqual(float(moved.mass()), 6.0, delta=TOLERANCE)
        self.assertCoordinatesAlmostEqual(
            moved.center().value(),
            (3.0, -1.5, 8.5),
        )

        translated_by_transform = shape.transform(runtime.translation(2, 3, 4))
        translated_by_legacy_adapter = shape.translate(2, 3, 4)
        self.assertCoordinatesAlmostEqual(
            translated_by_transform.center().value(),
            translated_by_legacy_adapter.center().value(),
        )
        self.assertAlmostEqual(
            float(translated_by_transform.mass()),
            float(translated_by_legacy_adapter.mass()),
            delta=TOLERANCE,
        )

    def test_zero_and_nonfinite_values_are_rejected(self):
        runtime = typed.Runtime.deferred(cache=False)
        invalid_factories = (
            lambda: runtime.quaternion(0, 0, 0, 0),
            lambda: runtime.quaternion(math.inf, 0, 0, 1),
            lambda: runtime.quaternion_axis_angle(runtime.vector(0, 0, 0), 1),
            lambda: runtime.quaternion_axis_angle(runtime.vector(math.nan, 0, 1), 1),
            lambda: runtime.quaternion_axis_angle(runtime.vector(0, 0, 1), math.inf),
            lambda: runtime.translation(math.nan, 0, 0),
            lambda: runtime.scale(0),
            lambda: runtime.scale(-0.0),
            lambda: runtime.scale(sys.float_info.min),
            lambda: runtime.scale(math.inf),
            lambda: runtime.scale(
                2,
                center=runtime.point(0, math.nan, 0),
            ),
            lambda: runtime.mirror(runtime.vector(0, 0, 0)),
            lambda: runtime.mirror(runtime.vector(0, math.inf, 1)),
            lambda: runtime.mirror(
                runtime.vector(0, 0, 1),
                origin=runtime.point(math.nan, 0, 0),
            ),
            lambda: runtime.scale(1e-320).inverse(),
        )

        for factory in invalid_factories:
            with self.subTest(factory=factory):
                with self.assertRaises(ValueError):
                    factory()

        smallest_ocp_scale = math.nextafter(sys.float_info.min, math.inf)
        self.assertEqual(
            runtime.scale(smallest_ocp_scale).to_ocp().ScaleFactor(),
            smallest_ocp_scale,
        )

        deferred = typed.Runtime.deferred(cache=False)
        mass = deferred.box(1).mass()
        zero = mass - mass
        invalid_quaternion = deferred.quaternion(zero, zero, zero, zero)
        norm = invalid_quaternion.norm()
        self.assertIsInstance(norm._state, Expression)
        with self.assertRaisesRegex(ValueError, "cannot be zero"):
            float(norm)

    def test_wrong_domain_types_are_rejected_at_the_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        quaternion = runtime.quaternion(0, 0, 0, 1)
        transform = runtime.identity_transform()
        point = runtime.point(1, 2, 3)
        shape = runtime.box(1)
        invalid_calls = (
            lambda: typed.Quaternion((1, 2, 3), runtime=runtime),
            lambda: runtime.quaternion(True, 0, 0, 1),
            lambda: runtime.translation(point),
            lambda: runtime.translation(1, 2),
            lambda: runtime.rotation(runtime.vector(0, 0, 1)),
            lambda: runtime.rotation(point, 1),
            lambda: runtime.scale(2, center=runtime.vector(0, 0, 0)),
            lambda: runtime.mirror(point),
            lambda: quaternion.rotate(point),
            lambda: quaternion * transform,
            lambda: transform * quaternion,
            lambda: transform.apply(runtime.point2(1, 2)),
            lambda: shape.transform(quaternion),
            lambda: typed.Quaternion.from_ocp(gp_Trsf(), runtime=runtime),
            lambda: typed.Transform.from_ocp(
                gp_Quaternion(),
                runtime=runtime,
            ),
        )

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaises(TypeError):
                    invalid_call()

    def test_handles_from_different_runtimes_cannot_be_mixed(self):
        first = typed.Runtime.deferred(cache=False)
        second = typed.Runtime.deferred(cache=False)
        first_quaternion = first.quaternion_axis_angle(first.vector(0, 0, 1), 0.5)
        second_quaternion = second.quaternion_axis_angle(second.vector(0, 0, 1), 0.5)
        first_transform = first.rotation(first_quaternion)
        second_transform = second.rotation(second_quaternion)
        invalid_calls = (
            lambda: first.quaternion(first.scalar(1), second.scalar(2), 3, 4),
            lambda: first.quaternion_axis_angle(second.vector(1, 0, 0), 1),
            lambda: first_quaternion * second_quaternion,
            lambda: first_quaternion.rotate(second.vector(1, 2, 3)),
            lambda: first.rotation(second_quaternion),
            lambda: first.translation(second.vector(1, 2, 3)),
            lambda: first.scale(second.scalar(2)),
            lambda: first.scale(2, center=second.point(1, 2, 3)),
            lambda: first.mirror(
                first.vector(0, 0, 1),
                origin=second.point(0, 0, 0),
            ),
            lambda: first_transform * second_transform,
            lambda: first_transform(second.point(1, 2, 3)),
            lambda: first.box(1).transform(second_transform),
        )

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaisesRegex(
                    ValueError,
                    "different typed runtimes",
                ):
                    invalid_call()

    def test_randomized_similarity_algebra_properties(self):
        runtime = typed.Runtime.deferred(cache=False)
        randomizer = random.Random(0x5EED_2021)

        def random_vector():
            return runtime.vector(
                randomizer.uniform(-5, 5),
                randomizer.uniform(-5, 5),
                randomizer.uniform(-5, 5),
            )

        def random_axis():
            while True:
                axis = random_vector()
                if float(axis.length()) > 0.25:
                    return axis

        def random_transform():
            scale = randomizer.uniform(0.2, 3.0)
            if randomizer.choice((False, True)):
                scale = -scale
            return (
                runtime.translation(random_vector())
                * runtime.rotation(
                    random_axis(),
                    randomizer.uniform(-math.pi, math.pi),
                )
                * runtime.scale(scale)
            )

        for iteration in range(50):
            with self.subTest(iteration=iteration):
                outer = random_transform()
                inner = random_transform()
                point = runtime.point(*random_vector().value())
                vector = random_vector()
                composed = outer * inner

                self.assertCoordinatesAlmostEqual(
                    composed(point).value(),
                    outer(inner(point)).value(),
                )
                self.assertCoordinatesAlmostEqual(
                    composed(vector).value(),
                    outer(inner(vector)).value(),
                )
                self.assertCoordinatesAlmostEqual(
                    inner.then(outer)(point).value(),
                    composed(point).value(),
                )
                self.assertCoordinatesAlmostEqual(
                    composed.inverse()(composed(point)).value(),
                    point.value(),
                )
                self.assertCoordinatesAlmostEqual(
                    composed.inverse()(composed(vector)).value(),
                    vector.value(),
                )

                displaced = point + vector
                self.assertCoordinatesAlmostEqual(
                    (composed(displaced) - composed(point)).value(),
                    composed(vector).value(),
                )

                quaternion = runtime.quaternion_axis_angle(
                    random_axis(),
                    randomizer.uniform(-math.pi, math.pi),
                )
                rotated = quaternion.rotate(vector)
                self.assertAlmostEqual(
                    float(rotated.length()),
                    float(vector.length()),
                    delta=TOLERANCE,
                )

                native_point = gp_Pnt(*point.value())
                native_point.Transform(composed.to_ocp())
                self.assertCoordinatesAlmostEqual(
                    composed(point).value(),
                    (
                        native_point.X(),
                        native_point.Y(),
                        native_point.Z(),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
