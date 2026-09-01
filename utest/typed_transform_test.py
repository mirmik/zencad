import math
import random
import sys
import unittest

from OCP.gp import gp_Pnt, gp_Quaternion, gp_Trsf, gp_Vec
from evalcache.v2 import CacheRecord, EvaluationMode, Expression

from zencad import geom as typed
from zencad.operation import DomainOperation, using_context


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
    def test_transform_family_is_declared_at_module_level(self):
        for name in (
            "quaternion",
            "quaternion_axis_angle",
            "identity_transform",
            "translation",
            "rotation",
            "scale",
            "mirror",
            "short_rotate",
            "identity_affine_transform",
            "affine_transform",
            "scaleXYZ",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        mass = context.call(typed.box, 1).mass()
        axis = context.call(typed.vector3, 0, 0, 1)
        offset = context.call(typed.vector3, mass, 0, 0)
        point = context.call(typed.point3, 0, 0, 0)
        with using_context(context):
            quaternion = typed.quaternion_axis_angle(axis, mass)
            values = (
                typed.translation(offset),
                typed.rotation(quaternion),
                typed.scale(mass, center=point),
                typed.mirror(offset, origin=point),
                typed.short_rotate(axis, offset),
                typed.scaleXYZ(mass, 1, 1, center=point),
            )

        self.assertTrue(all(value.context is context for value in values))
        self.assertEqual(events, [])
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.transform.translation",
                "zencad.typed.transform.rotation",
                "zencad.typed.transform.scale",
                "zencad.typed.transform.mirror",
                "zencad.typed.transform.shortest_rotation",
                "zencad.typed.affine.scale_xyz",
            ),
        )
        moved = context.call(typed.box, 1).transform(values[0])
        self.assertIs(type(moved), typed.Solid)
        self.assertEqual(moved._state.result.type_id, "zencad.typed.Solid.v1")

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
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=store,
                        progress_hooks=(events.append,),
                    )
                    shape = context.call(typed.box, 1, 2, 3)
                    mass = shape.mass()
                    center = shape.center()
                    axis = typed.Vector3(center.x, center.y, center.z)
                    quaternion = context.call(
                        typed.quaternion_axis_angle, axis, mass / 10
                    )
                    offset = typed.Vector3(center.x, center.y, center.z)
                    transform = (
                        context.call(typed.translation, offset)
                        * context.call(typed.rotation, quaternion)
                        * context.call(typed.scale, mass / 3, center=center)
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
                context = typed.Context(
                    mode=mode,
                    cache=True,
                    cache_store=store,
                    progress_hooks=(events.append,),
                )
                first = context.call(typed.quaternion, 0, 0, 2, 2)
                second = context.call(
                    typed.quaternion_axis_angle,
                    context.call(typed.vector, 0, 1, 0),
                    math.pi / 3,
                )
                quaternion = (first * second).inverse()
                transform = (
                    context.call(typed.translation, 1, 2, 3)
                    * context.call(typed.rotation, quaternion)
                    * context.call(
                        typed.scale,
                        -2,
                        center=context.call(typed.point, 3, 2, 1),
                    )
                    * context.call(
                        typed.mirror,
                        context.call(typed.vector, 0, 0, 1),
                        origin=context.call(typed.point, 0, 0, 2),
                    )
                )
                point = transform(context.call(typed.point, 4, 5, 6))
                vector = transform(context.call(typed.vector, 4, 5, 6))
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
        context = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        shape = context.call(typed.box, 2)
        mass = shape.mass()
        center = shape.center()
        axis = typed.Vector3(center.x, center.y, center.z)
        angle = mass / 16
        offset = typed.Vector3(center.x, mass / 8, center.z)
        quaternion = context.call(typed.quaternion_axis_angle, axis, angle)
        norm = quaternion.norm()
        translation = context.call(typed.translation, offset)
        rotation = context.call(typed.rotation, quaternion)
        scale = context.call(typed.scale, (mass / 4) * norm, center=center)
        transform = translation * rotation * scale
        point = transform(context.call(typed.point, 1, 2, 3))
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
        context = typed.Context.deferred(cache=False)
        point = context.call(typed.point, 1, 0, 0)
        move = context.call(typed.translation, 1, 0, 0)
        rotate = context.call(
            typed.rotation,
            context.call(typed.vector, 0, 0, 1),
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
        context = typed.Context.deferred(cache=False)
        x_rotation = context.call(
            typed.quaternion_axis_angle,
            context.call(typed.vector, 1, 0, 0),
            math.pi / 2,
        )
        y_rotation = context.call(
            typed.quaternion_axis_angle,
            context.call(typed.vector, 0, 1, 0),
            math.pi / 3,
        )
        vector = context.call(typed.vector, 2, -3, 4)

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

        positive = context.call(typed.quaternion, 1, 2, 3, 4)
        negative = context.call(typed.quaternion, -1, -2, -3, -4)
        self.assertEqual(positive, negative)
        self.assertEqual(positive.value(), negative.value())
        self.assertEqual(
            context.call(typed.quaternion, -1, 0, 0, 0).value(),
            (1.0, 0.0, 0.0, 0.0),
        )

        subnormal_axis = context.call(
            typed.quaternion_axis_angle,
            context.call(typed.vector, 5e-324, 0, 0),
            math.pi / 2,
        )
        self.assertCoordinatesAlmostEqual(
            subnormal_axis.rotate(context.call(typed.vector, 0, 1, 0)).value(),
            (0.0, 0.0, 1.0),
        )

        identity = typed.Quaternion.identity(context=context)
        self.assertEqual((identity * positive).value(), positive.value())
        self.assertEqual((positive * identity).value(), positive.value())
        transform = context.call(typed.translation, 1, 2, 3) * positive.to_transform()
        identity_transform = context.call(
            typed.identity_transform,
        )
        self.assertEqual((identity_transform * transform).matrix(), transform.matrix())
        self.assertEqual((transform * identity_transform).matrix(), transform.matrix())

    def test_point_and_vector_application_have_distinct_translation_semantics(self):
        context = typed.Context.deferred(cache=False)
        transform = (
            context.call(typed.translation, 10, -2, 7)
            * context.call(
                typed.rotation, context.call(typed.vector, 0, 0, 1), math.pi / 2
            )
            * context.call(typed.scale, 2)
        )
        point = context.call(typed.point, 1, 2, 3)
        vector = context.call(typed.vector, 1, 2, 3)

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
            context.call(typed.translation, 10, -2, 7)(vector),
            vector,
        )

    def test_transform_and_quaternion_inverses_round_trip(self):
        context = typed.Context.deferred(cache=False)
        quaternion = context.call(
            typed.quaternion_axis_angle, context.call(typed.vector, 2, -1, 4), 1.234
        )
        transform = (
            context.call(typed.translation, 3, -5, 7)
            * context.call(typed.rotation, quaternion)
            * context.call(
                typed.scale,
                -1.25,
                center=context.call(typed.point, 2, 1, -3),
            )
        )
        point = context.call(typed.point, -4, 8, 0.5)
        vector = context.call(typed.vector, 2, 3, -7)

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
            context.call(
                typed.identity_transform,
            ).matrix(),
        )

    def test_scale_about_center_supports_signed_scale(self):
        context = typed.Context.deferred(cache=False)
        center = context.call(typed.point, 1, 2, 3)
        scale = context.call(typed.scale, -2, center=center)

        self.assertCoordinatesAlmostEqual(scale(center).value(), center.value())
        self.assertCoordinatesAlmostEqual(
            scale(context.call(typed.point, 2, 4, 6)).value(),
            (-1.0, -2.0, -3.0),
        )
        self.assertCoordinatesAlmostEqual(
            scale(context.call(typed.vector, 1, 2, 3)).value(),
            (-2.0, -4.0, -6.0),
        )
        self.assertEqual(float(scale.scale), -2.0)

    def test_mirror_plane_is_an_involution(self):
        context = typed.Context.deferred(cache=False)
        mirror = context.call(
            typed.mirror,
            context.call(typed.vector, 0, 0, 2),
            origin=context.call(typed.point, 0, 0, 3),
        )
        point = context.call(typed.point, 1, 2, 5)
        vector = context.call(typed.vector, 1, 2, 3)

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
            context.call(
                typed.identity_transform,
            ).matrix(),
        )

    def test_ocp_round_trip_and_fresh_mutable_boundaries(self):
        context = typed.Context.deferred(cache=False)
        quaternion = context.call(
            typed.quaternion_axis_angle,
            context.call(typed.vector, 1, -2, 3),
            0.75,
        )
        transform = (
            context.call(typed.translation, 4, 5, -6)
            * context.call(typed.rotation, quaternion)
            * context.call(typed.scale, -2)
        )

        ocp_quaternion = quaternion.to_ocp()
        self.assertIsInstance(ocp_quaternion, gp_Quaternion)
        restored_quaternion = typed.Quaternion.from_ocp(
            ocp_quaternion,
            context=context,
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
            context=context,
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

        point = context.call(typed.point, 2, -1, 8)
        native_point = gp_Pnt(*point.value())
        native_point.Transform(transform.to_ocp())
        self.assertCoordinatesAlmostEqual(
            transform(point).value(),
            (native_point.X(), native_point.Y(), native_point.Z()),
        )

    def test_shape_transform_uses_the_typed_adapter(self):
        context = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 1, 2, 3)
        transform = context.call(typed.translation, 4, -2, 7) * context.call(
            typed.rotation, context.call(typed.vector, 0, 0, 1), math.pi / 2
        )
        moved = shape.transform(transform)

        self.assertIs(type(moved), typed.Solid)
        self.assertFalse(moved.native().IsNull())
        self.assertAlmostEqual(float(moved.mass()), 6.0, delta=TOLERANCE)
        self.assertCoordinatesAlmostEqual(
            moved.center().value(),
            (3.0, -1.5, 8.5),
        )

        translated_by_transform = shape.transform(
            context.call(typed.translation, 2, 3, 4)
        )
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
        context = typed.Context.deferred(cache=False)
        invalid_factories = (
            lambda: context.call(typed.quaternion, 0, 0, 0, 0),
            lambda: context.call(typed.quaternion, math.inf, 0, 0, 1),
            lambda: context.call(
                typed.quaternion_axis_angle, context.call(typed.vector, 0, 0, 0), 1
            ),
            lambda: context.call(
                typed.quaternion_axis_angle,
                context.call(typed.vector, math.nan, 0, 1),
                1,
            ),
            lambda: context.call(
                typed.quaternion_axis_angle,
                context.call(typed.vector, 0, 0, 1),
                math.inf,
            ),
            lambda: context.call(typed.translation, math.nan, 0, 0),
            lambda: context.call(typed.scale, 0),
            lambda: context.call(typed.scale, -0.0),
            lambda: context.call(typed.scale, sys.float_info.min),
            lambda: context.call(typed.scale, math.inf),
            lambda: context.call(
                typed.scale,
                2,
                center=context.call(typed.point, 0, math.nan, 0),
            ),
            lambda: context.call(typed.mirror, context.call(typed.vector, 0, 0, 0)),
            lambda: context.call(
                typed.mirror, context.call(typed.vector, 0, math.inf, 1)
            ),
            lambda: context.call(
                typed.mirror,
                context.call(typed.vector, 0, 0, 1),
                origin=context.call(typed.point, math.nan, 0, 0),
            ),
            lambda: context.call(typed.scale, 1e-320).inverse(),
        )

        for factory in invalid_factories:
            with self.subTest(factory=factory):
                with self.assertRaises(ValueError):
                    factory()

        smallest_ocp_scale = math.nextafter(sys.float_info.min, math.inf)
        self.assertEqual(
            context.call(typed.scale, smallest_ocp_scale).to_ocp().ScaleFactor(),
            smallest_ocp_scale,
        )

        deferred = typed.Context.deferred(cache=False)
        mass = deferred.call(typed.box, 1).mass()
        zero = mass - mass
        invalid_quaternion = deferred.call(typed.quaternion, zero, zero, zero, zero)
        norm = invalid_quaternion.norm()
        self.assertIsInstance(norm._state, Expression)
        with self.assertRaisesRegex(ValueError, "cannot be zero"):
            float(norm)

    def test_wrong_domain_types_are_rejected_at_the_boundary(self):
        context = typed.Context.deferred(cache=False)
        quaternion = context.call(typed.quaternion, 0, 0, 0, 1)
        transform = context.call(
            typed.identity_transform,
        )
        point = context.call(typed.point, 1, 2, 3)
        shape = context.call(typed.box, 1)
        invalid_calls = (
            lambda: typed.Quaternion((1, 2, 3), context=context),
            lambda: context.call(typed.quaternion, True, 0, 0, 1).value(),
            lambda: context.call(typed.translation, point),
            lambda: context.call(typed.translation, 1, 2),
            lambda: context.call(typed.rotation, context.call(typed.vector, 0, 0, 1)),
            lambda: context.call(typed.rotation, point, 1),
            lambda: context.call(
                typed.scale, 2, center=context.call(typed.vector, 0, 0, 0)
            ),
            lambda: context.call(typed.mirror, point),
            lambda: quaternion.rotate(point),
            lambda: quaternion * transform,
            lambda: transform * quaternion,
            lambda: transform.apply(context.call(typed.point2, 1, 2)),
            lambda: shape.transform(quaternion),
            lambda: typed.Quaternion.from_ocp(gp_Trsf(), context=context),
            lambda: typed.Transform.from_ocp(
                gp_Quaternion(),
                context=context,
            ),
        )

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaises(TypeError):
                    invalid_call()

    def test_handles_from_different_contexts_cannot_be_mixed(self):
        first = typed.Context.deferred(cache=False)
        second = typed.Context.deferred(cache=False)
        first_quaternion = first.call(
            typed.quaternion_axis_angle, first.call(typed.vector, 0, 0, 1), 0.5
        )
        second_quaternion = second.call(
            typed.quaternion_axis_angle, second.call(typed.vector, 0, 0, 1), 0.5
        )
        first_transform = first.call(typed.rotation, first_quaternion)
        second_transform = second.call(typed.rotation, second_quaternion)
        invalid_calls = (
            lambda: first.call(
                typed.quaternion,
                first.call(typed.scalar, 1),
                second.call(typed.scalar, 2),
                3,
                4,
            ),
            lambda: first.call(
                typed.quaternion_axis_angle, second.call(typed.vector, 1, 0, 0), 1
            ),
            lambda: first_quaternion * second_quaternion,
            lambda: first_quaternion.rotate(second.call(typed.vector, 1, 2, 3)),
            lambda: first.call(typed.rotation, second_quaternion),
            lambda: first.call(typed.translation, second.call(typed.vector, 1, 2, 3)),
            lambda: first.call(typed.scale, second.call(typed.scalar, 2)),
            lambda: first.call(
                typed.scale, 2, center=second.call(typed.point, 1, 2, 3)
            ),
            lambda: first.call(
                typed.mirror,
                first.call(typed.vector, 0, 0, 1),
                origin=second.call(typed.point, 0, 0, 0),
            ),
            lambda: first_transform * second_transform,
            lambda: first_transform(second.call(typed.point, 1, 2, 3)),
            lambda: first.call(typed.box, 1).transform(second_transform),
        )

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaisesRegex(
                    ValueError,
                    "different contexts",
                ):
                    invalid_call()

    def test_randomized_similarity_algebra_properties(self):
        context = typed.Context.deferred(cache=False)
        randomizer = random.Random(0x5EED_2021)

        def random_vector():
            return context.call(
                typed.vector,
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
                context.call(typed.translation, random_vector())
                * context.call(
                    typed.rotation,
                    random_axis(),
                    randomizer.uniform(-math.pi, math.pi),
                )
                * context.call(typed.scale, scale)
            )

        for iteration in range(50):
            with self.subTest(iteration=iteration):
                outer = random_transform()
                inner = random_transform()
                point = context.call(typed.point, *random_vector().value())
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

                quaternion = context.call(
                    typed.quaternion_axis_angle,
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
