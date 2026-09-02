import unittest

from zencad import geom as typed


class TypedShapeListTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = typed.Context.deferred(cache=False)

    def test_box_selectors_compose_and_preserve_stable_order(self) -> None:
        with typed.using_context(self.context):
            body = typed.box(10, 20, 30)
            edges = body.edges()
            vertical = edges.filter_by(typed.Axis.Z)
            long_edges = edges.longer_than(25)
            top_and_bottom = body.faces().normal_to(typed.Axis.Z).sort_by(typed.Axis.Z)

        self.assertIs(type(edges), typed.ShapeList)
        self.assertIs(typed.DeferredSequence, typed.ShapeList)
        self.assertEqual(len(vertical), 8)
        self.assertEqual(len(long_edges), 8)
        self.assertEqual(
            [round(float(face.center().z), 7) for face in top_and_bottom],
            [0.0, 30.0],
        )
        self.assertEqual(
            [edge.curvetype() for edge in vertical],
            ["line"] * len(vertical),
        )
        self.assertEqual(
            [float(edge.curve().range().length()) for edge in vertical],
            [30.0] * len(vertical),
        )

    def test_geometry_position_grouping_and_tolerance(self) -> None:
        with typed.using_context(self.context):
            body = typed.cylinder(5, 10)
            faces = body.faces()
            groups = faces.group_by(typed.GeomType)
            upper = faces.filter_by_position(typed.Axis.Z, 10).only()
            upper_from_plane = faces.filter_by(typed.Plane.xy(10)).only()
            loose = faces.normal_to((0, 1e-4, 1), tolerance=1e-3)
            strict = faces.normal_to((0, 1e-4, 1), tolerance=1e-5)

        self.assertEqual(
            tuple(groups),
            (typed.GeomType.CYLINDER, typed.GeomType.PLANE),
        )
        self.assertEqual(len(groups[typed.GeomType.CYLINDER]), 1)
        self.assertEqual(len(groups[typed.GeomType.PLANE]), 2)
        self.assertAlmostEqual(float(upper.center().z), 10)
        self.assertAlmostEqual(float(upper_from_plane.center().z), 10)
        self.assertEqual(len(loose), 2)
        self.assertEqual(len(strict), 0)

    def test_sort_largest_and_cardinality_errors_are_explicit(self) -> None:
        with typed.using_context(self.context):
            faces = typed.box(10, 20, 30).faces()
            nearest = faces.sort_by_distance((5, 10, 30))[0]
            largest = faces.largest()
            empty = faces.filter_by_position(typed.Axis.Z, 100)

        self.assertAlmostEqual(float(nearest.center().z), 30)
        self.assertAlmostEqual(float(largest.SurfaceProperties().mass), 600)
        self.assertEqual(len(empty), 0)
        with self.assertRaisesRegex(ValueError, "non-empty ShapeList"):
            empty.largest().native()
        with self.assertRaisesRegex(ValueError, "exactly one shape; got 0"):
            empty.only().native()
        with self.assertRaisesRegex(ValueError, "exactly one shape; got 6"):
            faces.only().native()

    def test_selectors_feed_modeling_operations_directly(self) -> None:
        with typed.using_context(self.context):
            body = typed.box(10)
            vertical_edges = body.edges().filter_by(typed.Axis.Z)
            x_faces = body.faces().normal_to(typed.Axis.X)
            filleted = typed.fillet(body, 1, vertical_edges)
            chamfered = typed.chamfer(body, 1, vertical_edges)
            drafted = typed.draft(body, x_faces, 0.05)

        self.assertGreater(float(filleted.mass()), 0)
        self.assertGreater(float(chamfered.mass()), 0)
        self.assertGreater(float(drafted.mass()), 0)

        with typed.using_context(self.context):
            foreign = typed.box(1).edges().filter_by(typed.Axis.Z)
            invalid = typed.fillet(body, 1, foreign)
            empty = body.edges().filter_by(typed.GeomType.CIRCLE)
        with self.assertRaisesRegex(ValueError, "does not belong to body"):
            invalid.mass().value()
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            typed.fillet(body, 1, empty).mass().value()

    def test_materialization_uses_the_expression_context(self) -> None:
        expression_context = typed.Context.deferred(cache=False)
        ambient_context = typed.Context.deferred(cache=False)

        with typed.using_context(expression_context):
            body = typed.box(10)
            vertical_edges = body.edges().filter_by(typed.Axis.Z)
            filleted = typed.fillet(body, 1, vertical_edges)

        with typed.using_context(ambient_context):
            self.assertGreater(float(filleted.mass()), 0)

    def test_composite_solid_selection_is_deterministic(self) -> None:
        with typed.using_context(self.context):
            composite = typed.union((typed.box(2), typed.box(2).right(4)))
            first = composite.faces().sort_by(typed.Axis.X)
            second = composite.faces().sort_by(typed.Axis.X)

        first_centers = [round(float(face.center().x), 7) for face in first]
        second_centers = [round(float(face.center().x), 7) for face in second]
        self.assertEqual(first_centers, second_centers)
        self.assertEqual(first_centers, sorted(first_centers))


if __name__ == "__main__":
    unittest.main()
