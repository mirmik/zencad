import unittest

from evalcache.v2 import EvaluationMode, Expression

from zencad import _typed as typed


class TypedTopologyCompatibilityTest(unittest.TestCase):
    def test_predicates_are_policy_independent_materialized_queries(self):
        observed = set()
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(mode=mode, cache=cache)
                    solid = context.call(typed.box, 1)
                    observed.add(
                        (
                            solid.shapetype(),
                            solid.is_solid(),
                            solid.is_volumed(),
                            solid.is_face(),
                        )
                    )
                    self.assertIs(type(solid), typed.Solid)
        self.assertEqual(observed, {("solid", True, True, False)})

    def test_predicate_call_is_an_explicit_materialization_boundary(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        solid = context.call(typed.box, context.call(typed.scalar, 2))

        self.assertIsInstance(solid._state, Expression)
        self.assertEqual(events, [])
        self.assertEqual(solid.shapetype(), "solid")
        self.assertTrue(events)

    def test_edge_wire_queries_and_conversion_preserve_typed_handles(self):
        context = typed.Context.deferred(cache=False)
        start = context.call(typed.point3, 0, 0, 0)
        finish = context.call(typed.point3, 1, 0, 0)
        edge = context.call(typed.segment, start, finish)
        wire = context.call(typed.polysegment,
            (start, context.call(typed.point3, 1, 0, 0), context.call(typed.point3, 0, 1, 0)),
            closed=True,
        )

        self.assertTrue(edge.is_edge())
        self.assertTrue(edge.is_wire_or_edge())
        self.assertFalse(edge.is_closed())
        self.assertEqual(wire.shapetype(), "wire")
        self.assertTrue(wire.is_wire())
        self.assertTrue(wire.is_closed())

        converted = edge.Wire_orEdgeToWire()
        identity = wire.to_wire()
        self.assertIs(type(converted), typed.Wire)
        self.assertIs(type(identity), typed.Wire)
        self.assertFalse(converted.native().IsNull())
        self.assertFalse(identity.native().IsNull())

        with self.assertRaisesRegex(TypeError, "only defined for Edge or Wire"):
            context.call(typed.box, 1).is_closed()

    def test_native_vertices_is_a_typed_topology_sequence(self):
        context = typed.Context.deferred(cache=False)
        vertices = context.call(typed.box, 1).native_vertices()

        self.assertIs(type(vertices), typed.DeferredSequence)
        self.assertEqual(len(vertices), 8)
        self.assertIs(type(vertices[0]), typed.Vertex)
        self.assertEqual(vertices[0].shapetype(), "vertex")

    def test_curve_parameter_records_are_named_graph_handles(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        line = context.call(typed.line, context.call(typed.point3, 1, 2, 3), context.call(typed.vector3, 1, 0, 0))
        circle = context.call(typed.circle_curve, 2)
        ellipse = context.call(typed.ellipse_curve, 3, 2)

        line_parameters = line.line_parameters()
        circle_parameters = circle.circle_parameters()
        ellipse_parameters = ellipse.ellipse_parameters()
        self.assertIs(type(line_parameters), typed.LineParameters)
        self.assertIs(type(circle_parameters), typed.CircleParameters)
        self.assertIs(type(ellipse_parameters), typed.EllipseParameters)
        self.assertEqual(events, [])

        self.assertEqual(line.curvetype(), "line")
        self.assertEqual(line_parameters.origin.value(), (1.0, 2.0, 3.0))
        self.assertEqual(line_parameters.direction.value(), (1.0, 0.0, 0.0))
        self.assertEqual(circle_parameters.center.value(), (0.0, 0.0, 0.0))
        self.assertEqual(float(circle_parameters.radius), 2.0)
        self.assertEqual(float(ellipse_parameters.major_radius), 3.0)
        self.assertEqual(float(ellipse_parameters.minor_radius), 2.0)

        with self.assertRaisesRegex(TypeError, "not a line"):
            circle.line_parameters().origin.value()

    def test_curve_projection_trimming_and_uniform_sampling(self):
        context = typed.Context.deferred(cache=False)
        line = context.call(typed.line, context.call(typed.point3, ), context.call(typed.vector3, 1, 0, 0))
        edge = line.trimmed_edge(0, 2)

        self.assertIs(type(edge), typed.Edge)
        start, finish = edge.endpoints()
        self.assertEqual(start.value(), (0.0, 0.0, 0.0))
        self.assertEqual(finish.value(), (2.0, 0.0, 0.0))
        self.assertAlmostEqual(
            float(edge.lower_distance_parameter(context.call(typed.point3, 0.75, 2, 0))),
            0.75,
        )

        circle = context.call(typed.circle_curve, 2)
        parameters = circle.uniform(4)
        points = circle.uniform_points(4)
        self.assertEqual(len(parameters), 4)
        self.assertTrue(all(type(value) is typed.Scalar for value in parameters))
        self.assertTrue(all(type(value) is typed.Point3 for value in points))
        self.assertAlmostEqual(float(parameters[0]), 0.0)
        self.assertAlmostEqual(float(parameters[-1]), 2 * 3.141592653589793)
        self.assertEqual(points[0].value(), (2.0, 0.0, 0.0))

        with self.assertRaisesRegex(ValueError, "positive int"):
            circle.uniform(0)
        with self.assertRaisesRegex(TypeError, "provided together"):
            circle.uniform(3, 0)

    def test_shape_curve_compatibility_methods_forward_to_typed_curve(self):
        context = typed.Context.deferred(cache=False)
        edge = context.call(typed.segment, context.call(typed.point3, ), context.call(typed.point3, 2, 0, 0))

        self.assertEqual(edge.curvetype(), "line")
        self.assertEqual(edge.d0(0.5).value(), (0.5, 0.0, 0.0))
        self.assertEqual(edge.value(1).value(), (1.0, 0.0, 0.0))
        self.assertEqual(edge.d1(0).value(), (1.0, 0.0, 0.0))
        self.assertIs(type(edge.line_parameters()), typed.LineParameters)
        self.assertIs(type(edge.trimmed_edge(0.25, 1.25)), typed.Edge)
        self.assertEqual(len(edge.uniform_points(3)), 3)

    def test_surface_and_volume_properties_are_named_graph_records(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        face = context.call(typed.rectangle, 2, 3)
        solid = context.call(typed.box, 2)
        surface = face.SurfaceProperties()
        volume = solid.VolumeProperties()

        self.assertIs(type(surface), typed.ShapeProperties)
        self.assertIs(type(volume), typed.ShapeProperties)
        self.assertIs(type(face.normal()), typed.Vector3)
        self.assertEqual(events, [])
        self.assertEqual(face.normal().value(), (0.0, 0.0, 1.0))
        self.assertAlmostEqual(float(surface.mass), 6.0)
        self.assertEqual(surface.center.value(), (1.0, 1.5, 0.0))
        self.assertAlmostEqual(float(volume.mass), 8.0)
        self.assertEqual(volume.center.value(), (1.0, 1.0, 1.0))
        self.assertTrue(events)

        self.assertIsNotNone(face.AdaptorSurface())
        edge = context.call(typed.segment, context.call(typed.point3, ), context.call(typed.point3, 1, 0, 0))
        self.assertIsNotNone(edge.AdaptorCurve())
        self.assertIsNotNone(edge.HCurveAdaptor())
        self.assertIsNotNone(edge.Curve())

    def test_modeling_compatibility_methods_return_typed_graph_handles(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        wire = context.call(typed.polysegment,
            (
                context.call(typed.point3, ),
                context.call(typed.point3, 2, 0, 0),
                context.call(typed.point3, 2, 2, 0),
                context.call(typed.point3, 0, 2, 0),
            ),
            closed=True,
        )
        face = wire.fill()
        solid = face.extrude(context.call(typed.scalar, 1), center=True)
        fillet = solid.fillet(0.1)
        chamfer = solid.chamfer(0.1)
        fillet2d = face.fillet2d(0.1)
        chamfer2d = face.chamfer2d(0.1)

        self.assertIs(type(face), typed.Face)
        self.assertIs(type(solid), typed.Shape)
        self.assertIs(type(fillet), typed.Shape)
        self.assertIs(type(chamfer), typed.Shape)
        self.assertIs(type(fillet2d), typed.Face)
        self.assertIs(type(chamfer2d), typed.Face)
        self.assertTrue(
            all(
                isinstance(value._state, Expression)
                for value in (face, solid, fillet, chamfer, fillet2d, chamfer2d)
            )
        )
        self.assertEqual(events, [])

        self.assertEqual(face.shapetype(), "face")
        self.assertEqual(solid.shapetype(), "solid")
        self.assertFalse(fillet.native().IsNull())
        self.assertFalse(chamfer.native().IsNull())
        self.assertFalse(fillet2d.native().IsNull())
        self.assertFalse(chamfer2d.native().IsNull())
        self.assertTrue(events)


if __name__ == "__main__":
    unittest.main()
