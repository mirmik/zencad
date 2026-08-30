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

from zencad import _typed as typed
from zencad.geom.shape import LazyObjectShape
from zencad.runtime.scene_protocol import decode_brep, encode_brep


def _points(runtime: typed.Runtime) -> tuple[typed.Point3, ...]:
    return (
        runtime.point(0, 0, 0),
        runtime.point(2, 0, 0),
        runtime.point(2, 3, 0),
        runtime.point(0, 3, 0),
    )


def _boolean_operands(
    runtime: typed.Runtime,
) -> tuple[typed.Solid, typed.Solid]:
    return runtime.box(2), runtime.box(2).translate(1, 0, 0)


class TypedShapeFactoriesTest(unittest.TestCase):
    def test_exact_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    points = _points(runtime)
                    edge = runtime.segment(points[0], points[1])
                    wire = runtime.polysegment(points, closed=True)
                    polygon = runtime.polygon(points)
                    rectangle = runtime.rectangle(2, 3, center=True)
                    box = runtime.box(runtime.vector(2, 3, 4), center=True)
                    sphere = runtime.sphere(2)

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
                    self.assertIs(box.unlazy(), box)

        self.assertEqual(len(observed_types), 1)

    def test_scalar_point_and_vector_factory_arguments_preserve_graph(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = runtime.box(2)
        side = seed.mass() / 4
        size = runtime.vector(side, side + 1, side + 2)
        origin = seed.center()
        x = runtime.vector(side, 0, 0)
        y = runtime.vector(0, side + 1, 0)

        solid = runtime.box(size)
        sphere = runtime.sphere(side)
        edge = runtime.segment(origin, origin + size)
        wire = runtime.polysegment(
            (origin, origin + x, origin + x + y, origin + y),
            closed=True,
        )
        face = runtime.polygon((origin, origin + x, origin + x + y, origin + y))
        rectangle = runtime.rectangle(side, side + 1)

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
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        point = runtime.point(0, 0, 0)

        with self.assertRaisesRegex(TypeError, "all three dimensions"):
            runtime.box(1, 2)
        with self.assertRaisesRegex(TypeError, "cannot be combined"):
            runtime.box(runtime.vector(1, 2, 3), 2, 3)
        with self.assertRaisesRegex(TypeError, "center must be bool"):
            runtime.box(1, center="x")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "expects only Point3"):
            runtime.polysegment((point, (1, 0, 0)))  # type: ignore[list-item]
        with self.assertRaisesRegex(ValueError, "at least 3 points"):
            runtime.polygon((point, point))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.segment(point, other.point(1, 0, 0))


class TypedShapeBooleansTest(unittest.TestCase):
    def test_binary_booleans_return_general_shape_across_policy_matrix(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    left, right = _boolean_operands(runtime)
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
                        self.assertIs(value.unlazy(), value)

        self.assertEqual(len(observed_types), 1)

    def test_empty_boolean_result_remains_a_valid_general_shape(self):
        runtime = typed.Runtime.deferred(cache=False)
        box = runtime.box(1)

        empty_difference = box - box
        empty_intersection = box ^ box.translate(10, 0, 0)

        for value in (empty_difference, empty_intersection):
            self.assertIs(type(value), typed.Shape)
            self.assertFalse(value.native().IsNull())
            self.assertAlmostEqual(float(value.mass()), 0.0)

    def test_boolean_operands_must_be_shapes_from_one_runtime(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        shape = runtime.box(1)

        for operation in (
            lambda: shape + 1,  # type: ignore[operator]
            lambda: shape - 1,  # type: ignore[operator]
            lambda: shape ^ 1,  # type: ignore[operator]
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(TypeError, "expects Shape"):
                    operation()

        for operation in (
            lambda: shape + other.box(1),
            lambda: shape - other.box(1),
            lambda: shape ^ other.box(1),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, "different typed runtimes"):
                    operation()

    def test_fresh_runtime_restores_boolean_brep_without_recomputing_inputs(self):
        store = MemoryCacheStore()

        first_events = []
        first = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_result = first.box(3) + first.sphere(first.box(2).mass() / 8)
        first_native = first_result.native()
        self.assertFalse(first_native.IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second_result = second.box(3) + second.sphere(second.box(2).mass() / 8)
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
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    outer = runtime.box(runtime.vector(10, 10, 10), center=True)
                    radius = outer.mass() / 500
                    cutter = runtime.sphere(radius).translate(0, 0, 5)
                    modeled = (outer - cutter).transform(
                        runtime.rotation(runtime.vector(0, 0, 1), 0.25)
                    )
                    vertex = modeled.vertices()[0]
                    point = vertex.point()
                    offset = runtime.vector(modeled.mass() / 1000, point.y, 0)
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
                    self.assertFalse(
                        any(
                            isinstance(value, LazyObjectShape)
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
