import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
import numpy
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE

from zencad import geom as typed
from zencad.operation import using_context


class TypedCoordinateCoercionCompatibilityTest(unittest.TestCase):
    def test_legacy_coordinate_sequences_work_in_all_policies(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    with using_context(context):
                        polygon = typed.polygon([(0, 0), (4, 0), (4, 3), (0, 3)])
                        segment = typed.segment((0, 0), (1, 2, 3))
                        interpolated = typed.interpolate(
                            [(0, 0), (1, 0), (2, 1), (3, 1, 0)],
                            tangs=[(1, 0), None, None, (1, 0, 0)],
                        )
                        polyline = typed.polysegment(
                            [(0, 0), (2, 0), (2, 2), (0, 2)],
                            closed=True,
                        )
                        rounded = typed.rounded_polysegment(
                            [(0, 0), (4, 0), (4, 4)],
                            r=0.5,
                        )

                    results = (polygon, segment, interpolated, polyline, rounded)
                    self.assertTrue(
                        all(result.context is context for result in results)
                    )
                    self.assertEqual(polygon.native().ShapeType(), TopAbs_FACE)
                    self.assertEqual(segment.native().ShapeType(), TopAbs_EDGE)
                    self.assertEqual(interpolated.native().ShapeType(), TopAbs_EDGE)
                    self.assertEqual(polyline.native().ShapeType(), TopAbs_WIRE)
                    self.assertEqual(rounded.native().ShapeType(), TopAbs_WIRE)
                    self.assertEqual(segment.endpoints()[0].value(), (0.0, 0.0, 0.0))
                    self.assertEqual(segment.endpoints()[1].value(), (1.0, 2.0, 3.0))

    def test_raw_and_typed_points_share_the_selected_context(self):
        context = typed.Context.deferred(cache=False)
        point = context.call(typed.point3, 1, 0, 0)

        wire = context.call(
            typed.polysegment,
            ((0, 0), point, (1, 1, 0)),
        )

        self.assertIs(wire.context, context)
        self.assertEqual(
            tuple(endpoint.value() for endpoint in wire.endpoints()),
            ((0.0, 0.0, 0.0), (1.0, 1.0, 0.0)),
        )

        moved = point.moveY(3)
        self.assertIs(type(moved), typed.Point3)
        self.assertIs(moved.context, context)
        self.assertEqual(moved.value(), (1.0, 3.0, 0.0))

        transformed_wire = (
            context.call(typed.move, 1, 2, 3) * context.call(typed.rotateZ, 0.25)
        )(wire)
        self.assertIs(type(transformed_wire), typed.Wire)
        self.assertIs(transformed_wire.context, context)
        self.assertFalse(transformed_wire.native().IsNull())

    def test_numpy_coordinates_and_negated_centers_remain_legacy_compatible(self):
        context = typed.Context.deferred(cache=False)
        with using_context(context):
            coordinates = numpy.asarray((1, 2, 3), dtype=numpy.float64)
            point = typed.point3(coordinates)
            moved = typed.box(2, center=True).translate(-point)

        self.assertEqual(point.value(), (1.0, 2.0, 3.0))
        self.assertIs(type(-point), typed.Point3)
        self.assertEqual((-point).value(), (-1.0, -2.0, -3.0))
        for actual, expected in zip(moved.center().value(), (-1.0, -2.0, -3.0)):
            self.assertAlmostEqual(actual, expected)

    def test_vertex_coordinates_and_rounding_references_are_compatible(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            with self.subTest(mode=mode):
                context = typed.Context(mode=mode, cache=False)
                face = context.call(
                    typed.polygon,
                    [(0, 0), (4, 0), (4, 4), (0, 4)],
                )
                vertices = tuple(face.vertices())
                selected = [vertex for vertex in vertices if vertex.x < 0.1]

                self.assertEqual(len(selected), 2)
                self.assertTrue(all(vertex.context is context for vertex in vertices))
                self.assertTrue(
                    all(
                        isinstance(coordinate, typed.Scalar)
                        for vertex in vertices
                        for coordinate in (vertex.x, vertex.y, vertex.z)
                    )
                )

                rounded = face.fillet2d(0.25, selected[:1])
                rounded_from_tuple = face.fillet2d(
                    0.25,
                    [selected[1].point().value()],
                )

                self.assertEqual(rounded.native().ShapeType(), TopAbs_FACE)
                self.assertEqual(rounded_from_tuple.native().ShapeType(), TopAbs_FACE)

    def test_invalid_coordinate_sequence_is_rejected_at_materialization(self):
        edge = typed.segment((0, 0), (1, 2, 3, 4))

        with self.assertRaisesRegex(TypeError, "at most three coordinates"):
            edge.native()


if __name__ == "__main__":
    unittest.main()
