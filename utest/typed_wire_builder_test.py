import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_WIRE

from zencad import geom as typed


class TypedWireBuilderTest(unittest.TestCase):
    def test_fluent_builder_is_policy_independent(self):
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
                    builder = (
                        context.call(typed.wire_builder, defrel=True)
                        .l(4, 0)
                        .line(0, 3)
                        .segment(-4, 0)
                        .close()
                    )
                    wire = builder.build()
                    observed_types.add((type(builder), type(wire)))

                    self.assertIsInstance(builder, typed.WireBuilder)
                    self.assertIsInstance(wire, typed.Wire)
                    self.assertIsInstance(builder.doit(), typed.Wire)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])
                    self.assertEqual(wire.native().ShapeType(), TopAbs_WIRE)
                    self.assertTrue(wire.is_closed())
                    self.assertEqual(len(wire.edges()), 4)

        self.assertEqual(observed_types, {(typed.WireBuilder, typed.Wire)})

    def test_restart_prepare_and_legacy_coordinate_forms(self):
        context = typed.Context.deferred(cache=False)
        builder = typed.WireBuilder(context=context, defrel=True)

        self.assertEqual(
            typed.WireBuilder.collect_point(1, 2, 3),
            (1, 2, 3),
        )
        prepared = builder.prepare(((1, 2), (3, 4)))
        self.assertEqual([point.value() for point in prepared], [(1, 2, 0), (3, 4, 0)])
        wire = builder.restart(10, 20).l(2, 0).l(0, 2).doit()

        self.assertEqual(len(wire.edges()), 2)
        self.assertEqual(wire.endpoints()[0].value(), (10, 20, 0))
        self.assertEqual(wire.endpoints()[1].value(), (12, 22, 0))

    def test_curve_operations_remain_inside_the_graph(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = context.call(typed.box, 2).mass() / 8
        arc = context.call(typed.wire_builder, start=(unit * 10, 0, 0)).arc(
            (0, 0, 0),
            unit * 10,
            -math.pi / 2,
        )
        ellipse = context.call(typed.wire_builder, start=(unit * 10, 0, 0)).elliptic_arc(
            (0, 0, 0),
            unit * 10,
            unit * 5,
            math.pi / 2,
            0,
        )
        points = context.call(typed.wire_builder, ).arc_by_points((1, 1), (2, 0))
        interpolated = (
            context.call(typed.wire_builder, )
            .segment((1, 0))
            .interpolate(((2, 1), (3, 0)), approx=True)
        )
        closed = context.call(typed.wire_builder, ).segment((2, 0)).close(True, True)

        self.assertEqual(events, [])
        for builder in (arc, ellipse, points, interpolated, closed):
            self.assertFalse(builder.build().native().IsNull())
        self.assertTrue(events)
        self.assertAlmostEqual(arc.current.x.value(), 0)
        self.assertAlmostEqual(arc.current.y.value(), -10)
        self.assertAlmostEqual(ellipse.current.x.value(), 0)
        self.assertAlmostEqual(ellipse.current.y.value(), 5)

    def test_svg_endpoint_arcs_cover_flags_and_radii_order(self):
        context = typed.Context.deferred(cache=False)
        short = context.call(typed.wire_builder, ).svg_elliptic_arc(
            10, 5, 0.3, False, True, 10, 5
        )
        tall = context.call(typed.wire_builder, ).svg_elliptic_arc(
            5, 10, 0.3, False, True, 10, 5
        )
        large = context.call(typed.wire_builder, ).svg_elliptic_arc(
            10, 5, 0.3, True, True, 10, 5
        )
        circle = context.call(typed.wire_builder, ).svg_circle_arc(
            8, 0, False, False, 10, 5
        )
        plane = context.call(typed.wire_builder, ).plane_circle_arc(
            8, math.pi, False, True, 10, 5
        )

        for builder in (short, tall, large, circle, plane):
            wire = builder.build()
            self.assertEqual(len(wire.edges()), 1)
            self.assertAlmostEqual(wire.endpoints()[0].x.value(), 0)
            self.assertAlmostEqual(wire.endpoints()[0].y.value(), 0)
            self.assertAlmostEqual(wire.endpoints()[1].x.value(), 10)
            self.assertAlmostEqual(wire.endpoints()[1].y.value(), 5)
        short_range = short.edges[0].range()
        large_range = large.edges[0].range()
        self.assertLess(
            short_range.upper.value() - short_range.lower.value(),
            math.pi,
        )
        self.assertGreater(
            large_range.upper.value() - large_range.lower.value(),
            math.pi,
        )

    def test_builder_wire_restores_from_shared_cache(self):
        store = MemoryCacheStore()

        def build(context: typed.Context) -> tuple[typed.WireBuilder, typed.Wire]:
            builder = (
                context.call(typed.wire_builder, )
                .segment((2, 0))
                .svg_circle_arc(2, 0, False, True, 2, 4)
                .segment((0, 4))
                .close()
            )
            return builder, builder.build()

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first_builder, first_wire = build(first)
        self.assertFalse(first_builder.edges[1].native().IsNull())
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
        second_builder, second_wire = build(second)
        self.assertFalse(second_builder.edges[1].native().IsNull())
        self.assertFalse(second_wire.native().IsNull())
        hits = {
            event.operation_id
            for event in second_events
            if event.kind is EvaluationEventKind.CACHE_HIT
        }
        self.assertIn("zencad.typed.make_wire", hits)
        self.assertIn("zencad.typed.svg_elliptic_arc", hits)

    def test_invalid_builder_inputs_are_explicit(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        self.assertIsInstance(typed.WireBuilder(), typed.WireBuilder)
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.wire_builder, other.call(typed.point3, 0, 0, 0))
        with self.assertRaisesRegex(ValueError, "has no edges"):
            context.call(typed.wire_builder, ).build()
        with self.assertRaisesRegex(ValueError, "at least one point"):
            context.call(typed.wire_builder, ).interpolate(())
        with self.assertRaisesRegex(ValueError, "needs an edge"):
            context.call(typed.wire_builder, ).interpolate(((1, 0),), approx=True)
        with self.assertRaisesRegex(ValueError, "non-zero"):
            context.call(typed.wire_builder, ).svg_circle_arc(
                0, 0, False, True, 1, 1
            ).build().native()


if __name__ == "__main__":
    unittest.main()
