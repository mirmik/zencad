import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.Geom import Geom_Curve
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.TopAbs import TopAbs_EDGE, TopAbs_WIRE

from zencad import geom as typed
from zencad.operation import DomainOperation, using_context


def _points(context: typed.Context) -> tuple[typed.Point3, ...]:
    return (
        context.call(typed.point3, 0, 0, 0),
        context.call(typed.point3, 1, 0, 0),
        context.call(typed.point3, 2, 1, 0),
        context.call(typed.point3, 3, 1, 0),
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
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        points = _points(context)
        with using_context(context):
            line = typed.line(points[0], context.call(typed.vector3, 1, 0, 0))
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
            curve2 = typed.segment2(
                context.call(typed.point2, 0, 0), context.call(typed.point2, 1, 0)
            )
            ellipse2 = typed.ellipse2(2, 1)
            trimmed2 = typed.trim_curve2(curve2, 0, 1)
            polyline = typed.polysegment(points)
            transformed = circle.transform(context.call(typed.moveX, 1))
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
        self.assertTrue(all(value.context is context for value in values))
        self.assertTrue(all(value.context is context for value in aliases))
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
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    points = _points(context)
                    tangents = (
                        context.call(typed.vector3, 1, 0, 0),
                        None,
                        None,
                        context.call(typed.vector3, 1, 0, 0),
                    )
                    interpolate_curve = context.call(
                        typed.interpolate_curve, points, tangents
                    )
                    interpolate_edge = context.call(typed.interpolate, points, tangents)
                    bezier_curve = context.call(
                        typed.bezier_curve, points[:3], (1, 2, 1)
                    )
                    bezier_edge = context.call(typed.bezier, points[:3])
                    bspline_curve = context.call(
                        typed.bspline_curve,
                        points,
                        (0, 0.5, 1),
                        (3, 1, 3),
                        2,
                    )
                    bspline_edge = context.call(
                        typed.bspline,
                        points,
                        (0, 0.5, 1),
                        (3, 1, 3),
                        2,
                    )
                    arc = context.call(
                        typed.circle_arc, points[0], points[1], points[2]
                    )
                    rounded = context.call(typed.rounded_polysegment, points, 0.2)
                    helix = context.call(typed.helix, 2, 5, step=1)
                    wire = context.call(
                        typed.make_wire,
                        context.call(typed.segment, points[0], points[1]),
                        context.call(typed.segment, points[1], points[2]),
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
        context = typed.Context.deferred(cache=False)
        points = _points(context)
        curve = context.call(typed.interpolate_curve, points)
        bezier = context.call(typed.bezier_curve, points[:3], weights=(1, 2, 1))
        bspline = context.call(
            typed.bspline_curve,
            points,
            knots=(0, 0.5, 1),
            muls=(3, 1, 3),
            degree=2,
        )
        circle = context.call(typed.circle_curve, 2)
        moved = circle.transform(context.call(typed.moveX, 3))
        half_circle = circle.edge((0, math.pi))
        interval_edge = context.call(typed.make_edge, circle, circle.range())

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
        context = typed.Context.deferred(cache=False)
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, 2, 0, 0),
            context.call(typed.point3, 2, 2, 0),
            context.call(typed.point3, 0, 2, 0),
        )
        edges = tuple(
            context.call(typed.segment, points[index], points[index + 1])
            for index in range(3)
        )
        variadic = context.call(typed.make_wire, *edges)
        sequence = context.call(typed.make_wire, edges)
        rounded_open = context.call(typed.rounded_polysegment, points, r=0.25)
        rounded_closed = context.call(
            typed.rounded_polysegment, points, r=0.25, closed=True
        )
        right_helix = context.call(typed.helix, r=2, h=5, step=1)
        left_helix = context.call(typed.helix, r=2, h=5, pitch=0.2, left=True)

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
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = context.call(typed.box, 2).mass() / 8
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, unit, 0, 0),
            context.call(typed.point3, unit * 2, unit, 0),
            context.call(typed.point3, unit * 3, unit, 0),
        )
        curve = context.call(typed.bezier_curve, points[:3], (unit, unit * 2, unit))
        bspline = context.call(
            typed.bspline_curve,
            points,
            (0, unit / 2, unit),
            (3, 1, 3),
            2,
        )
        edge = curve.edge((0, unit))
        rounded = context.call(typed.rounded_polysegment, points, unit / 5)
        helix = context.call(typed.helix, unit * 2, unit * 5, step=unit)

        self.assertEqual(events, [])
        for value in (curve, bspline):
            self.assertIsInstance(value.native(), Geom_Curve)
        for value in (edge, rounded, helix):
            self.assertFalse(value.native().IsNull())
        self.assertTrue(events)

    def test_curve_and_wire_artifacts_restore_from_cache(self):
        store = MemoryCacheStore()

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_curve = first.call(typed.bezier_curve, _points(first)[:3], (1, 2, 1))
        first_wire = first.call(typed.helix, 2, 5, step=1)
        self.assertIsInstance(first_curve.native(), Geom_Curve)
        self.assertFalse(first_wire.native().IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second_curve = second.call(typed.bezier_curve, _points(second)[:3], (1, 2, 1))
        second_wire = second.call(typed.helix, 2, 5, step=1)
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
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        points = _points(context)

        with self.assertRaisesRegex(ValueError, "at least 2 points"):
            context.call(typed.interpolate_curve, points[:1]).native()
        with self.assertRaisesRegex(ValueError, "match point count"):
            context.call(
                typed.interpolate_curve, points, (context.call(typed.vector3, 1, 0, 0),)
            ).native()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.interpolate_curve, (points[0], other.call(typed.point3, 1, 0, 0))
            )
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            context.call(typed.bezier_curve, points[:3], ()).native()
        with self.assertRaisesRegex(ValueError, "equal length"):
            context.call(typed.bspline_curve, points, (0, 1), (3,), 2).native()
        with self.assertRaisesRegex(TypeError, "two scalar bounds"):
            context.call(
                typed.make_edge, context.call(typed.circle_curve, 1), (0, 1, 2)
            ).native()
        with self.assertRaisesRegex(ValueError, "at least one Edge or Wire"):
            context.call(typed.make_wire).native()
        with self.assertRaises(TypeError):
            context.call(typed.make_wire, context.call(typed.box, 1)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "requires step or pitch"):
            context.call(typed.helix, 1, 2).native()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.circle_curve, 1).transform(other.call(typed.moveX, 1))


if __name__ == "__main__":
    unittest.main()
