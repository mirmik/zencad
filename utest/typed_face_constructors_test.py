import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE

from zencad import geom as typed
from zencad.operation import DomainOperation, using_context


def _rectangle_points(context: typed.Context) -> tuple[typed.Point3, ...]:
    return (
        context.call(typed.point3, 0, 0, 0),
        context.call(typed.point3, 4, 0, 0),
        context.call(typed.point3, 4, 3, 0),
        context.call(typed.point3, 0, 3, 0),
    )


def _surface_grid(
    context: typed.Context,
) -> tuple[tuple[typed.Point3, ...], ...]:
    return (
        (context.call(typed.point3, 0, 0, 0), context.call(typed.point3, 0, 2, 0)),
        (context.call(typed.point3, 2, 0, 0), context.call(typed.point3, 2, 2, 1)),
        (context.call(typed.point3, 4, 0, 0), context.call(typed.point3, 4, 2, 0)),
    )


class TypedFaceConstructorsTest(unittest.TestCase):
    def test_face_family_is_declared_at_module_level(self):
        for name in (
            "circle",
            "ellipse",
            "fill",
            "interpolate2",
            "fix_face",
            "infplane",
            "ruled",
            "widewire",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        points = _rectangle_points(context)
        grid = _surface_grid(context)
        with using_context(context):
            polygon = typed.polygon(points)
            polygon_wire = typed.polygon(points, wire=True)
            rectangle = typed.rectangle(4, 3)
            rectangle_wire = typed.rectangle_wire(4, 3)
            square = typed.square(3)
            ngon = typed.ngon(3, 6)
            circle = typed.circle(3)
            ellipse = typed.ellipse(4, 2, wire=True)
            filled = typed.fill(polygon_wire)
            interpolated = typed.interpolate2(grid)
            fixed = typed.fix_face(rectangle)
            plane = typed.infplane()
            ruled = typed.ruled(
                context.call(typed.segment, points[0], points[1]),
                context.call(typed.segment, points[3], points[2]),
            )
            wide = typed.widewire(polygon_wire, 0.2)

        values = (
            polygon,
            polygon_wire,
            rectangle,
            rectangle_wire,
            square,
            ngon,
            circle,
            ellipse,
            filled,
            interpolated,
            fixed,
            plane,
            ruled,
            wide,
        )
        self.assertTrue(all(value.context is context for value in values))
        self.assertEqual(events, [])
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.polygon",
                "zencad.typed.polysegment",
                "zencad.typed.rectangle",
                "zencad.typed.polysegment",
                "zencad.typed.rectangle",
                "zencad.typed.polygon",
                "zencad.typed.face.circle",
                "zencad.typed.face.ellipse",
                "zencad.typed.face.fill",
                "zencad.typed.face.interpolate2",
                "zencad.typed.face.fix",
                "zencad.typed.face.infplane",
                "zencad.typed.face.ruled",
                "zencad.typed.face.widewire",
            ),
        )

    def test_planar_factories_are_policy_independent(self):
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
                    points = _rectangle_points(context)
                    polygon = context.call(typed.polygon, points)
                    polygon_wire = context.call(typed.polygon, points, wire=True)
                    rectangle = context.call(typed.rectangle, 4, 3, center=True)
                    rectangle_wire = context.call(typed.rectangle, 4, 3, True, True)
                    square = context.call(typed.square, 3)
                    square_wire = context.call(typed.square, 3, wire=True)
                    ngon = context.call(typed.ngon, 3, 6)
                    ngon_wire = context.call(typed.ngon, 3, 6, True)
                    circle = context.call(typed.circle, 3)
                    circle_edge = context.call(
                        typed.circle, 3, (-math.pi / 2, math.pi / 2), True
                    )
                    circle_sector = context.call(typed.circle, 3, math.pi / 2)
                    ellipse = context.call(typed.ellipse, 2, 4)
                    ellipse_edge = context.call(typed.ellipse, 4, 2, wire=True)
                    ellipse_sector = context.call(typed.ellipse, 4, 2, (-1, 1))
                    filled = context.call(typed.fill, polygon_wire)
                    fixed = context.call(typed.fix_face, rectangle)
                    plane = context.call(
                        typed.infplane,
                    )
                    ruled = context.call(
                        typed.ruled,
                        context.call(typed.segment, points[0], points[1]),
                        context.call(typed.segment, points[3], points[2]),
                    )
                    interpolated = context.call(
                        typed.interpolate2, _surface_grid(context)
                    )

                    values = (
                        polygon,
                        polygon_wire,
                        rectangle,
                        rectangle_wire,
                        square,
                        square_wire,
                        ngon,
                        ngon_wire,
                        circle,
                        circle_edge,
                        circle_sector,
                        ellipse,
                        ellipse_edge,
                        ellipse_sector,
                        filled,
                        fixed,
                        plane,
                        ruled,
                        interpolated,
                    )
                    policy_types = tuple(type(value) for value in values)
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Face,
                            typed.Wire,
                            typed.Face,
                            typed.Wire,
                            typed.Face,
                            typed.Wire,
                            typed.Face,
                            typed.Wire,
                            typed.Face,
                            typed.Edge,
                            typed.Face,
                            typed.Face,
                            typed.Edge,
                            typed.Face,
                            typed.Face,
                            typed.Face,
                            typed.Face,
                            typed.Face,
                            typed.Face,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    natives = tuple(value.native() for value in values)
                    self.assertTrue(all(not native.IsNull() for native in natives))
                    self.assertEqual(natives[1].ShapeType(), TopAbs_WIRE)
                    self.assertEqual(natives[9].ShapeType(), TopAbs_EDGE)
                    self.assertTrue(
                        all(
                            native.ShapeType() == TopAbs_FACE
                            for index, native in enumerate(natives)
                            if index not in {1, 3, 5, 7, 9, 12}
                        )
                    )

        self.assertEqual(len(observed_types), 1)

    def test_conic_and_hole_geometry_is_truthful(self):
        context = typed.Context.deferred(cache=False)
        circle = context.call(typed.circle, 3)
        ellipse = context.call(typed.ellipse, 2, 4)
        circle_sector = context.call(typed.circle, 3, math.pi / 2)
        ellipse_sector = context.call(typed.ellipse, 2, 4, (-math.pi / 2, math.pi / 2))
        descending_edge = context.call(
            typed.circle, 3, (math.pi / 2, -math.pi / 2), True
        )
        outer = context.call(typed.rectangle, 10, 8, center=True, wire=True)
        inner = context.call(typed.rectangle, 4, 2, center=True, wire=True)
        holed = context.call(typed.fill, (outer, inner))

        self.assertAlmostEqual(circle.SurfaceProperties().mass.value(), math.pi * 9)
        self.assertAlmostEqual(ellipse.SurfaceProperties().mass.value(), math.pi * 8)
        self.assertAlmostEqual(
            circle_sector.SurfaceProperties().mass.value(), math.pi * 9 / 4
        )
        self.assertAlmostEqual(
            ellipse_sector.SurfaceProperties().mass.value(), math.pi * 4
        )
        self.assertAlmostEqual(descending_edge.endpoints()[0].y.value(), 3)
        self.assertAlmostEqual(descending_edge.endpoints()[1].y.value(), -3)
        self.assertAlmostEqual(holed.SurfaceProperties().mass.value(), 72)
        self.assertEqual(len(holed.edges()), 8)
        ellipse_bounds = ellipse.boundbox().value()
        self.assertAlmostEqual(ellipse_bounds.xmax - ellipse_bounds.xmin, 4, delta=1e-6)
        self.assertAlmostEqual(ellipse_bounds.ymax - ellipse_bounds.ymin, 8, delta=1e-6)
        self.assertGreater(circle.normal().z.value(), 0)
        self.assertGreater(ellipse.normal().z.value(), 0)

    def test_graph_scalars_and_points_remain_deferred(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = context.call(typed.box, 2).mass() / 8
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, unit * 4, 0, 0),
            context.call(typed.point3, unit * 4, unit * 3, 0),
            context.call(typed.point3, 0, unit * 3, 0),
        )
        polygon = context.call(typed.polygon, points)
        rectangle = context.call(typed.rectangle, unit * 4, unit * 3)
        circle = context.call(typed.circle, unit * 3)
        ellipse = context.call(typed.ellipse, unit * 2, unit * 4)
        ngon = context.call(typed.ngon, unit * 3, 5)

        self.assertEqual(events, [])
        for face in (polygon, rectangle, circle, ellipse, ngon):
            self.assertFalse(face.native().IsNull())
        self.assertTrue(events)

    def test_widewire_preserves_graph_and_truthful_shape_type(self):
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
                    unit = context.call(typed.box, 2).mass() / 8
                    spine = context.call(
                        typed.make_wire,
                        context.call(
                            typed.segment,
                            context.call(typed.point3, 0, 0, 0),
                            context.call(typed.point3, unit * 10, 0, 0),
                        ),
                        context.call(
                            typed.segment,
                            context.call(typed.point3, unit * 10, 0, 0),
                            context.call(typed.point3, unit * 10, unit * 10, 0),
                        ),
                    )
                    wide = context.call(typed.widewire, spine, unit)
                    square_ends = context.call(
                        typed.widewire,
                        context.call(
                            typed.segment,
                            context.call(typed.point3, 0, 0, 0),
                            context.call(typed.point3, unit * 10, 0, 0),
                        ),
                        unit,
                        circled_joints=False,
                        circled_ends=False,
                    )

                    observed_types.add((type(wide), type(square_ends)))
                    self.assertIs(type(wide), typed.Shape)
                    self.assertIs(type(square_ends), typed.Shape)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertAlmostEqual(
                        square_ends.SurfaceProperties().mass.value(),
                        20,
                    )
                    self.assertGreater(
                        wide.SurfaceProperties().mass.value(),
                        40,
                    )
                    self.assertEqual(len(wide.faces()), 1)

        self.assertEqual(observed_types, {(typed.Shape, typed.Shape)})

    def test_face_artifacts_restore_from_shared_cache(self):
        store = MemoryCacheStore()

        def values(context: typed.Context) -> tuple[typed.Face, ...]:
            points = _rectangle_points(context)
            return (
                context.call(typed.circle, 3, math.pi / 2),
                context.call(typed.ellipse, 2, 4),
                context.call(
                    typed.fill, context.call(typed.rectangle, 4, 3, wire=True)
                ),
                context.call(typed.interpolate2, _surface_grid(context)),
                context.call(
                    typed.ruled,
                    context.call(typed.segment, points[0], points[1]),
                    context.call(typed.segment, points[3], points[2]),
                ),
            )

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        for value in values(first):
            self.assertFalse(value.native().IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        for value in values(second):
            self.assertFalse(value.native().IsNull())
        hits = {
            event.operation_id
            for event in second_events
            if event.kind is EvaluationEventKind.CACHE_HIT
        }
        self.assertTrue(
            {
                "zencad.typed.face.circle",
                "zencad.typed.face.ellipse",
                "zencad.typed.face.fill",
                "zencad.typed.face.interpolate2",
                "zencad.typed.face.ruled",
            }.issubset(hits)
        )

    def test_widewire_artifact_restores_from_shared_cache(self):
        store = MemoryCacheStore()

        def value(context: typed.Context) -> typed.Shape:
            return context.call(
                typed.widewire,
                context.call(
                    typed.segment,
                    context.call(typed.point3, 0, 0, 0),
                    context.call(typed.point3, 10, 0, 0),
                ),
                1,
            )

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_value = value(first)
        self.assertFalse(first_value.native().IsNull())
        self.assertAlmostEqual(
            first_value.SurfaceProperties().mass.value(), 20 + math.pi
        )
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second_value = value(second)
        self.assertFalse(second_value.native().IsNull())
        self.assertAlmostEqual(
            second_value.SurfaceProperties().mass.value(), 20 + math.pi
        )
        self.assertIn(
            "zencad.typed.face.widewire",
            {
                event.operation_id
                for event in second_events
                if event.kind is EvaluationEventKind.CACHE_HIT
            },
        )

    def test_invalid_inputs_fail_at_the_typed_boundary(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        points = _rectangle_points(context)

        with self.assertRaisesRegex(ValueError, "at least 3"):
            context.call(typed.ngon, 1, 2)
        with self.assertRaisesRegex(ValueError, "distinct"):
            context.call(typed.circle, 2, (1, 1)).native()
        with self.assertRaisesRegex(ValueError, "positive"):
            context.call(typed.ellipse, 0, 2).native()
        with self.assertRaises(TypeError):
            context.call(typed.fill, context.call(typed.box, 1)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "at least two rows"):
            context.call(typed.interpolate2, (_surface_grid(context)[0],)).native()
        with self.assertRaisesRegex(ValueError, "rectangular"):
            context.call(
                typed.interpolate2, (_surface_grid(context)[0], points[:3])
            ).native()
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            context.call(typed.interpolate2, _surface_grid(context), 5, 3).native()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.ruled,
                context.call(typed.segment, points[0], points[1]),
                other.call(
                    typed.segment,
                    other.call(typed.point3, 0, 1),
                    other.call(typed.point3, 1, 1),
                ),
            )
        with self.assertRaises(TypeError):
            context.call(typed.widewire, context.call(typed.box, 1), 1).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "must be bool"):
            context.call(
                typed.widewire,
                context.call(typed.segment, points[0], points[1]),
                1,
                circled_joints=1,  # type: ignore[arg-type]
            ).native()
        with self.assertRaisesRegex(ValueError, "positive"):
            context.call(
                typed.widewire, context.call(typed.segment, points[0], points[1]), 0
            ).native()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.widewire,
                other.call(
                    typed.segment,
                    other.call(typed.point3, 0, 0),
                    other.call(typed.point3, 1, 0),
                ),
                1,
            )


if __name__ == "__main__":
    unittest.main()
