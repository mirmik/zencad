import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID, TopAbs_WIRE
from OCP.TopoDS import (
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Solid,
    TopoDS_Wire,
)

from zencad import geom as typed
from zencad.runtime.scene_protocol import decode_brep, encode_brep


def _points(context: typed.Context) -> tuple[typed.Point3, ...]:
    return (
        context.call(typed.point, 0, 0, 0),
        context.call(typed.point, 2, 0, 0),
        context.call(typed.point, 2, 3, 0),
        context.call(typed.point, 0, 3, 0),
    )


def _boolean_operands(
    context: typed.Context,
) -> tuple[typed.Solid, typed.Solid]:
    return context.call(typed.box, 2), context.call(typed.box, 2).translate(1, 0, 0)


class TypedShapeFactoriesTest(unittest.TestCase):
    def test_exact_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    points = _points(context)
                    edge = context.call(typed.segment, points[0], points[1])
                    wire = context.call(typed.polysegment, points, closed=True)
                    polygon = context.call(typed.polygon, points)
                    rectangle = context.call(typed.rectangle, 2, 3, center=True)
                    box = context.call(
                        typed.box, context.call(typed.vector, 2, 3, 4), center=True
                    )
                    sphere = context.call(typed.sphere, 2)

                    policy_types = tuple(
                        type(value)
                        for value in (edge, wire, polygon, rectangle, box, sphere)
                    )
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Edge,
                            typed.Wire,
                            typed.Face,
                            typed.Face,
                            typed.Solid,
                            typed.Solid,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    native_values = (
                        edge.native(),
                        wire.native(),
                        polygon.native(),
                        rectangle.native(),
                        box.native(),
                        sphere.native(),
                    )
                    self.assertEqual(
                        tuple(type(value) for value in native_values),
                        (
                            TopoDS_Edge,
                            TopoDS_Wire,
                            TopoDS_Face,
                            TopoDS_Face,
                            TopoDS_Solid,
                            TopoDS_Solid,
                        ),
                    )
                    self.assertEqual(
                        tuple(value.ShapeType() for value in native_values),
                        (
                            TopAbs_EDGE,
                            TopAbs_WIRE,
                            TopAbs_FACE,
                            TopAbs_FACE,
                            TopAbs_SOLID,
                            TopAbs_SOLID,
                        ),
                    )
                    self.assertTrue(all(not value.IsNull() for value in native_values))
                    self.assertAlmostEqual(float(box.mass()), 24.0)
                    self.assertAlmostEqual(
                        float(sphere.mass()), 4 / 3 * 3.141592653589793 * 8
                    )
                    self.assertEqual(len(wire.edges()), 4)
                    for coordinate in rectangle.center().value():
                        self.assertAlmostEqual(coordinate, 0.0)

        self.assertEqual(len(observed_types), 1)

    def test_scalar_point_and_vector_factory_arguments_preserve_graph(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = context.call(typed.box, 2)
        side = seed.mass() / 4
        size = context.call(typed.vector, side, side + 1, side + 2)
        origin = seed.center()
        x = context.call(typed.vector, side, 0, 0)
        y = context.call(typed.vector, 0, side + 1, 0)

        solid = context.call(typed.box, size)
        sphere = context.call(typed.sphere, side)
        edge = context.call(typed.segment, origin, origin + size)
        wire = context.call(
            typed.polysegment,
            (origin, origin + x, origin + x + y, origin + y),
            closed=True,
        )
        face = context.call(
            typed.polygon, (origin, origin + x, origin + x + y, origin + y)
        )
        rectangle = context.call(typed.rectangle, side, side + 1)

        self.assertEqual(events, [])
        self.assertAlmostEqual(float(solid.mass()), 24.0)
        self.assertAlmostEqual(float(sphere.mass()), 4 / 3 * 3.141592653589793 * 8)
        self.assertEqual(
            {
                tuple(round(coordinate, 12) for coordinate in vertex.point().value())
                for vertex in edge.vertices()
            },
            {(1.0, 1.0, 1.0), (3.0, 4.0, 5.0)},
        )
        self.assertEqual(len(wire.edges()), 4)
        self.assertEqual(len(face.edges()), 4)
        self.assertEqual(
            tuple(round(coordinate, 12) for coordinate in rectangle.center().value()),
            (1.0, 1.5, 0.0),
        )
        self.assertTrue(events)

    def test_invalid_factory_inputs_fail_at_the_typed_boundary(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        point = context.call(typed.point, 0, 0, 0)

        with self.assertRaisesRegex(TypeError, "all three dimensions"):
            context.call(typed.box, 1, 2).native()
        with self.assertRaisesRegex(TypeError, "cannot be combined"):
            context.call(typed.box, context.call(typed.vector, 1, 2, 3), 2, 3).native()
        with self.assertRaisesRegex(TypeError, "center must be bool, str, or None"):
            context.call(typed.box, 1, center=1.5).native()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            context.call(typed.polysegment, (point, (1, 0, 0))).native()  # type: ignore[list-item]
        with self.assertRaisesRegex(ValueError, "at least 3 points"):
            context.call(typed.polygon, (point, point)).native()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.segment, point, other.call(typed.point, 1, 0, 0))


class TypedShapeBooleansTest(unittest.TestCase):
    def test_binary_booleans_return_general_shape_across_policy_matrix(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    left, right = _boolean_operands(context)
                    union = left + right
                    difference = left - right
                    intersection = left ^ right

                    policy_types = tuple(
                        type(value) for value in (union, difference, intersection)
                    )
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (typed.Shape, typed.Shape, typed.Shape),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertAlmostEqual(float(union.mass()), 12.0)
                    self.assertAlmostEqual(float(difference.mass()), 4.0)
                    self.assertAlmostEqual(float(intersection.mass()), 4.0)
                    for value in (union, difference, intersection):
                        native = value.native()
                        self.assertIs(type(native), TopoDS_Shape)
                        self.assertFalse(native.IsNull())

        self.assertEqual(len(observed_types), 1)

    def test_empty_boolean_result_remains_a_valid_general_shape(self):
        context = typed.Context.deferred(cache=False)
        box = context.call(typed.box, 1)

        empty_difference = box - box
        empty_intersection = box ^ box.translate(10, 0, 0)

        for value in (empty_difference, empty_intersection):
            self.assertIs(type(value), typed.Shape)
            self.assertFalse(value.native().IsNull())
            self.assertAlmostEqual(float(value.mass()), 0.0)

    def test_boolean_operands_must_be_shapes_from_one_context(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 1)

        for operation in (
            lambda: (shape + 1).native(),  # type: ignore[operator]
            lambda: (shape - 1).native(),  # type: ignore[operator]
            lambda: (shape ^ 1).native(),  # type: ignore[operator]
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(TypeError):
                    operation()

        for operation in (
            lambda: shape + other.call(typed.box, 1),
            lambda: shape - other.call(typed.box, 1),
            lambda: shape ^ other.call(typed.box, 1),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, "different contexts"):
                    operation()

    def test_fresh_context_restores_boolean_brep_without_recomputing_inputs(self):
        store = MemoryCacheStore()

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_result = first.call(typed.box, 3) + first.call(
            typed.sphere, first.call(typed.box, 2).mass() / 8
        )
        first_native = first_result.native()
        self.assertFalse(first_native.IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second_result = second.call(typed.box, 3) + second.call(
            typed.sphere, second.call(typed.box, 2).mass() / 8
        )
        second_native = second_result.native()

        self.assertFalse(second_native.IsNull())
        hits = [
            event
            for event in second_events
            if event.kind is EvaluationEventKind.CACHE_HIT
        ]
        self.assertEqual(
            [event.operation_id for event in hits],
            ["zencad.typed.shape.union"],
        )
        shape_records = [
            record
            for record in store.records.values()
            if record.serializer_id == "zencad.shape.brep-artifact.v1"
        ]
        self.assertGreaterEqual(len(shape_records), 3)
        self.assertTrue(
            all(
                record.value.artifacts[0].name == "shape.brep"
                for record in shape_records
            )
        )

    def test_representative_model_crosses_only_explicit_boundaries(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    outer = context.call(
                        typed.box, context.call(typed.vector, 10, 10, 10), center=True
                    )
                    radius = outer.mass() / 500
                    cutter = context.call(typed.sphere, radius).translate(0, 0, 5)
                    modeled = (outer - cutter).transform(
                        context.call(
                            typed.rotation, context.call(typed.vector, 0, 0, 1), 0.25
                        )
                    )
                    vertex = modeled.vertices()[0]
                    point = vertex.point()
                    offset = context.call(
                        typed.vector, modeled.mass() / 1000, point.y, 0
                    )
                    result = modeled.translate(offset)

                    policy_types = tuple(
                        type(value)
                        for value in (
                            outer,
                            cutter,
                            modeled,
                            vertex,
                            point,
                            offset,
                            result,
                        )
                    )
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Solid,
                            typed.Solid,
                            typed.Shape,
                            typed.Vertex,
                            typed.Point3,
                            typed.Vector3,
                            typed.Shape,
                        ),
                    )
                    self.assertTrue(
                        all(
                            not hasattr(value, "unlazy")
                            for value in (
                                outer,
                                cutter,
                                modeled,
                                vertex,
                                point,
                                offset,
                                result,
                            )
                        )
                    )
                    native = result.native()
                    self.assertFalse(native.IsNull())
                    payload = encode_brep(native)
                    self.assertFalse(decode_brep(payload).IsNull())

        self.assertEqual(len(observed_types), 1)


if __name__ == "__main__":
    unittest.main()
