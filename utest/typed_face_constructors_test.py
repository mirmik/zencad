import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE

from zencad import _typed as typed


def _rectangle_points(runtime: typed.Runtime) -> tuple[typed.Point3, ...]:
    return (
        runtime.point3(0, 0, 0),
        runtime.point3(4, 0, 0),
        runtime.point3(4, 3, 0),
        runtime.point3(0, 3, 0),
    )


def _surface_grid(
    runtime: typed.Runtime,
) -> tuple[tuple[typed.Point3, ...], ...]:
    return (
        (runtime.point3(0, 0, 0), runtime.point3(0, 2, 0)),
        (runtime.point3(2, 0, 0), runtime.point3(2, 2, 1)),
        (runtime.point3(4, 0, 0), runtime.point3(4, 2, 0)),
    )


class TypedFaceConstructorsTest(unittest.TestCase):
    def test_planar_factories_are_policy_independent(self):
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
                    points = _rectangle_points(runtime)
                    polygon = runtime.polygon(points)
                    polygon_wire = runtime.polygon(points, wire=True)
                    rectangle = runtime.rectangle(4, 3, center=True)
                    rectangle_wire = runtime.rectangle(4, 3, True, True)
                    square = runtime.square(3)
                    square_wire = runtime.square(3, wire=True)
                    ngon = runtime.ngon(3, 6)
                    ngon_wire = runtime.ngon(3, 6, True)
                    circle = runtime.circle(3)
                    circle_edge = runtime.circle(3, (-math.pi / 2, math.pi / 2), True)
                    circle_sector = runtime.circle(3, math.pi / 2)
                    ellipse = runtime.ellipse(2, 4)
                    ellipse_edge = runtime.ellipse(4, 2, wire=True)
                    ellipse_sector = runtime.ellipse(4, 2, (-1, 1))
                    filled = runtime.fill(polygon_wire)
                    fixed = runtime.fix_face(rectangle)
                    plane = runtime.infplane()
                    ruled = runtime.ruled(
                        runtime.segment(points[0], points[1]),
                        runtime.segment(points[3], points[2]),
                    )
                    interpolated = runtime.interpolate2(_surface_grid(runtime))

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
        runtime = typed.Runtime.deferred(cache=False)
        circle = runtime.circle(3)
        ellipse = runtime.ellipse(2, 4)
        circle_sector = runtime.circle(3, math.pi / 2)
        ellipse_sector = runtime.ellipse(2, 4, (-math.pi / 2, math.pi / 2))
        descending_edge = runtime.circle(3, (math.pi / 2, -math.pi / 2), True)
        outer = runtime.rectangle(10, 8, center=True, wire=True)
        inner = runtime.rectangle(4, 2, center=True, wire=True)
        holed = runtime.fill((outer, inner))

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
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = runtime.box(2).mass() / 8
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(unit * 4, 0, 0),
            runtime.point3(unit * 4, unit * 3, 0),
            runtime.point3(0, unit * 3, 0),
        )
        polygon = runtime.polygon(points)
        rectangle = runtime.rectangle(unit * 4, unit * 3)
        circle = runtime.circle(unit * 3)
        ellipse = runtime.ellipse(unit * 2, unit * 4)
        ngon = runtime.ngon(unit * 3, 5)

        self.assertEqual(events, [])
        for face in (polygon, rectangle, circle, ellipse, ngon):
            self.assertFalse(face.native().IsNull())
        self.assertTrue(events)

    def test_face_artifacts_restore_from_shared_cache(self):
        store = MemoryCacheStore()

        def values(runtime: typed.Runtime) -> tuple[typed.Face, ...]:
            points = _rectangle_points(runtime)
            return (
                runtime.circle(3, math.pi / 2),
                runtime.ellipse(2, 4),
                runtime.fill(runtime.rectangle(4, 3, wire=True)),
                runtime.interpolate2(_surface_grid(runtime)),
                runtime.ruled(
                    runtime.segment(points[0], points[1]),
                    runtime.segment(points[3], points[2]),
                ),
            )

        first_events = []
        first = typed.Runtime.deferred(
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
        second = typed.Runtime.deferred(
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

    def test_invalid_inputs_fail_at_the_typed_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        points = _rectangle_points(runtime)

        with self.assertRaisesRegex(ValueError, "at least 3"):
            runtime.ngon(1, 2)
        with self.assertRaisesRegex(ValueError, "distinct"):
            runtime.circle(2, (1, 1)).native()
        with self.assertRaisesRegex(ValueError, "positive"):
            runtime.ellipse(0, 2).native()
        with self.assertRaisesRegex(TypeError, "only Edge or Wire"):
            runtime.fill(runtime.box(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "at least two rows"):
            runtime.interpolate2((_surface_grid(runtime)[0],))
        with self.assertRaisesRegex(ValueError, "rectangular"):
            runtime.interpolate2((_surface_grid(runtime)[0], points[:3]))
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            runtime.interpolate2(_surface_grid(runtime), 5, 3)
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.ruled(
                runtime.segment(points[0], points[1]),
                other.segment(other.point3(0, 1), other.point3(1, 1)),
            )


if __name__ == "__main__":
    unittest.main()
