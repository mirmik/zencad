import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.Geom import Geom_Curve
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.TopAbs import TopAbs_EDGE, TopAbs_WIRE

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_runtime


def _points(runtime: typed.Runtime) -> tuple[typed.Point3, ...]:
    return (
        runtime.point3(0, 0, 0),
        runtime.point3(1, 0, 0),
        runtime.point3(2, 1, 0),
        runtime.point3(3, 1, 0),
    )


class TypedCurveWireConstructorsTest(unittest.TestCase):
    def test_curve_and_wire_family_is_declared_at_module_level(self):
        for name in (
            "line",
            "circle_curve",
            "ellipse_curve",
            "interpolate_curve",
            "bezier_curve",
            "bspline_curve",
            "make_edge",
            "circle_arc",
            "make_wire",
            "rounded_polysegment",
            "helix",
            "segment2",
            "ellipse2",
            "trim_curve2",
            "segment",
            "polysegment",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        points = _points(runtime)
        with using_runtime(runtime):
            line = typed.line(points[0], runtime.vector3(1, 0, 0))
            circle = typed.circle_curve(2)
            ellipse = typed.ellipse_curve(2, 1)
            interpolated = typed.interpolate_curve(points)
            bezier = typed.bezier_curve(points[:3])
            bspline = typed.bspline_curve(points, (0, 0.5, 1), (3, 1, 3), 2)
            edge = typed.make_edge(circle)
            arc = typed.circle_arc(points[0], points[1], points[2])
            segment = typed.segment(points[0], points[1])
            wire = typed.make_wire(segment)
            rounded = typed.rounded_polysegment(points, 0.2)
            helix = typed.helix(2, 5, step=1)
            curve2 = typed.segment2(runtime.point2(0, 0), runtime.point2(1, 0))
            ellipse2 = typed.ellipse2(2, 1)
            trimmed2 = typed.trim_curve2(curve2, 0, 1)
            polyline = typed.polysegment(points)
            transformed = circle.transform(runtime.moveX(1))
            trimmed_edge = line.trimmed_edge(0, 1)
            method_edge = line.edge()
            rotated2 = curve2.rotate(0.5)
            method_trimmed2 = curve2.trim(0, 1)
            recovered_curve = edge.curve()
            aliases = (
                typed.interpolate(points),
                typed.bezier(points),
                typed.bspline(points, (0, 1), (3, 3), 2),
            )

        values = (
            line,
            circle,
            ellipse,
            interpolated,
            bezier,
            bspline,
            edge,
            arc,
            segment,
            wire,
            rounded,
            helix,
            curve2,
            ellipse2,
            trimmed2,
            polyline,
        )
        self.assertTrue(all(value.runtime is runtime for value in values))
        self.assertTrue(all(value.runtime is runtime for value in aliases))
        self.assertEqual(events, [])
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.line",
                "zencad.typed.circle_curve",
                "zencad.typed.ellipse_curve",
                "zencad.typed.interpolate_curve",
                "zencad.typed.bezier_curve",
                "zencad.typed.bspline_curve",
                "zencad.typed.make_edge",
                "zencad.typed.circle_arc",
                "zencad.typed.segment",
                "zencad.typed.make_wire",
                "zencad.typed.rounded_polysegment",
                "zencad.typed.helix",
                "zencad.typed.segment2",
                "zencad.typed.ellipse2",
                "zencad.typed.trim_curve2",
                "zencad.typed.polysegment",
            ),
        )
        self.assertEqual(
            (
                transformed._state.operation_id,
                trimmed_edge._state.operation_id,
                method_edge._state.operation_id,
                rotated2._state.operation_id,
                method_trimmed2._state.operation_id,
                recovered_curve._state.operation_id,
            ),
            (
                "zencad.typed.curve.transform",
                "zencad.typed.curve.trimmed_edge",
                "zencad.typed.make_edge",
                "zencad.typed.curve2.rotate",
                "zencad.typed.trim_curve2",
                "zencad.typed.edge.curve",
            ),
        )
        self.assertTrue(all(type(value) is typed.Edge for value in aliases))

    def test_curve_and_wire_factories_are_policy_independent(self):
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
                    tangents = (
                        runtime.vector3(1, 0, 0),
                        None,
                        None,
                        runtime.vector3(1, 0, 0),
                    )
                    interpolate_curve = runtime.interpolate_curve(points, tangents)
                    interpolate_edge = runtime.interpolate(points, tangents)
                    bezier_curve = runtime.bezier_curve(points[:3], (1, 2, 1))
                    bezier_edge = runtime.bezier(points[:3])
                    bspline_curve = runtime.bspline_curve(
                        points,
                        (0, 0.5, 1),
                        (3, 1, 3),
                        2,
                    )
                    bspline_edge = runtime.bspline(
                        points,
                        (0, 0.5, 1),
                        (3, 1, 3),
                        2,
                    )
                    arc = runtime.circle_arc(points[0], points[1], points[2])
                    rounded = runtime.rounded_polysegment(points, 0.2)
                    helix = runtime.helix(2, 5, step=1)
                    wire = runtime.make_wire(
                        runtime.segment(points[0], points[1]),
                        runtime.segment(points[1], points[2]),
                    )

                    values = (
                        interpolate_curve,
                        interpolate_edge,
                        bezier_curve,
                        bezier_edge,
                        bspline_curve,
                        bspline_edge,
                        arc,
                        rounded,
                        helix,
                        wire,
                    )
                    policy_types = tuple(type(value) for value in values)
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Curve,
                            typed.Edge,
                            typed.Curve,
                            typed.Edge,
                            typed.Curve,
                            typed.Edge,
                            typed.Edge,
                            typed.Wire,
                            typed.Wire,
                            typed.Wire,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    for curve in (interpolate_curve, bezier_curve, bspline_curve):
                        self.assertIsInstance(curve.native(), Geom_Curve)
                    for edge in (interpolate_edge, bezier_edge, bspline_edge, arc):
                        self.assertEqual(edge.native().ShapeType(), TopAbs_EDGE)
                    for result in (rounded, helix, wire):
                        self.assertEqual(result.native().ShapeType(), TopAbs_WIRE)

        self.assertEqual(len(observed_types), 1)

    def test_curve_geometry_transform_and_edge_interval(self):
        runtime = typed.Runtime.deferred(cache=False)
        points = _points(runtime)
        curve = runtime.interpolate_curve(points)
        bezier = runtime.bezier_curve(points[:3], weights=(1, 2, 1))
        bspline = runtime.bspline_curve(
            points,
            knots=(0, 0.5, 1),
            muls=(3, 1, 3),
            degree=2,
        )
        circle = runtime.circle_curve(2)
        moved = circle.transform(runtime.moveX(3))
        half_circle = circle.edge((0, math.pi))
        interval_edge = runtime.make_edge(circle, circle.range())

        self.assertEqual(curve.curvetype(), "bspline")
        self.assertEqual(bezier.curvetype(), "bezier")
        self.assertEqual(bspline.curvetype(), "bspline")
        self.assertEqual(curve.point(curve.range().lower).value(), points[0].value())
        self.assertEqual(curve.point(curve.range().upper).value(), points[-1].value())
        self.assertEqual(moved.point(0).value(), (5.0, 0.0, 0.0))
        self.assertEqual(half_circle.shapetype(), "edge")
        self.assertEqual(interval_edge.shapetype(), "edge")
        self.assertIsInstance(circle.AdaptorCurve(), GeomAdaptor_Curve)
        self.assertIsInstance(circle.HCurveAdaptor(), GeomAdaptor_Curve)
        self.assertIsNot(circle.Curve(), circle.Curve())

    def test_wire_geometry_and_legacy_call_forms(self):
        runtime = typed.Runtime.deferred(cache=False)
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(2, 0, 0),
            runtime.point3(2, 2, 0),
            runtime.point3(0, 2, 0),
        )
        edges = tuple(
            runtime.segment(points[index], points[index + 1]) for index in range(3)
        )
        variadic = runtime.make_wire(*edges)
        sequence = runtime.make_wire(edges)
        rounded_open = runtime.rounded_polysegment(points, r=0.25)
        rounded_closed = runtime.rounded_polysegment(points, r=0.25, closed=True)
        right_helix = runtime.helix(r=2, h=5, step=1)
        left_helix = runtime.helix(r=2, h=5, pitch=0.2, left=True)

        self.assertEqual(len(variadic.edges()), 3)
        self.assertEqual(len(sequence.edges()), 3)
        self.assertFalse(rounded_open.is_closed())
        self.assertTrue(rounded_closed.is_closed())
        self.assertAlmostEqual(
            abs(
                right_helix.endpoints()[1].z.value()
                - right_helix.endpoints()[0].z.value()
            ),
            5.0,
        )
        self.assertAlmostEqual(
            abs(
                left_helix.endpoints()[1].z.value()
                - left_helix.endpoints()[0].z.value()
            ),
            5.0,
        )

    def test_scalar_inputs_remain_in_the_graph(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = runtime.box(2).mass() / 8
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(unit, 0, 0),
            runtime.point3(unit * 2, unit, 0),
            runtime.point3(unit * 3, unit, 0),
        )
        curve = runtime.bezier_curve(points[:3], (unit, unit * 2, unit))
        bspline = runtime.bspline_curve(
            points,
            (0, unit / 2, unit),
            (3, 1, 3),
            2,
        )
        edge = curve.edge((0, unit))
        rounded = runtime.rounded_polysegment(points, unit / 5)
        helix = runtime.helix(unit * 2, unit * 5, step=unit)

        self.assertEqual(events, [])
        for value in (curve, bspline):
            self.assertIsInstance(value.native(), Geom_Curve)
        for value in (edge, rounded, helix):
            self.assertFalse(value.native().IsNull())
        self.assertTrue(events)

    def test_curve_and_wire_artifacts_restore_from_cache(self):
        store = MemoryCacheStore()

        first_events = []
        first = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_curve = first.bezier_curve(_points(first)[:3], (1, 2, 1))
        first_wire = first.helix(2, 5, step=1)
        self.assertIsInstance(first_curve.native(), Geom_Curve)
        self.assertFalse(first_wire.native().IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second_curve = second.bezier_curve(_points(second)[:3], (1, 2, 1))
        second_wire = second.helix(2, 5, step=1)
        self.assertIsInstance(second_curve.native(), Geom_Curve)
        self.assertFalse(second_wire.native().IsNull())
        hits = {
            event.operation_id
            for event in second_events
            if event.kind is EvaluationEventKind.CACHE_HIT
        }
        self.assertIn("zencad.typed.bezier_curve", hits)
        self.assertIn("zencad.typed.helix", hits)

    def test_invalid_inputs_fail_before_or_at_the_resolved_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        points = _points(runtime)

        with self.assertRaisesRegex(ValueError, "at least 2 points"):
            runtime.interpolate_curve(points[:1])
        with self.assertRaisesRegex(ValueError, "match point count"):
            runtime.interpolate_curve(points, (runtime.vector3(1, 0, 0),))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.interpolate_curve((points[0], other.point3(1, 0, 0)))
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            runtime.bezier_curve(points[:3], ())
        with self.assertRaisesRegex(ValueError, "equal length"):
            runtime.bspline_curve(points, (0, 1), (3,), 2)
        with self.assertRaisesRegex(TypeError, "two scalar bounds"):
            runtime.make_edge(runtime.circle_curve(1), (0, 1, 2))
        with self.assertRaisesRegex(ValueError, "at least one Edge or Wire"):
            runtime.make_wire()
        with self.assertRaisesRegex(TypeError, "only Edge or Wire"):
            runtime.make_wire(runtime.box(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "requires step or pitch"):
            runtime.helix(1, 2)
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.circle_curve(1).transform(other.moveX(1))


if __name__ == "__main__":
    unittest.main()
