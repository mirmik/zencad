import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_context


class TypedBooleanOperationsTest(unittest.TestCase):
    def test_boolean_family_is_declared_at_module_level(self):
        for name in ("empty_shape", "union", "intersect", "difference", "section"):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        left = context.call(typed.box, 2)
        right = context.call(typed.box, 2).translate(1, 0, 0)
        results = (
            typed.union(left, right),
            typed.intersect((left, right)),
            typed.intersection(left, right),
            typed.difference(left, right),
            typed.section(left, 1),
        )
        with using_context(context):
            zero = typed.empty_shape()
            legacy_zero = typed.nullshape()

        self.assertTrue(all(result.context is context for result in results))
        self.assertIs(zero.context, context)
        self.assertIs(legacy_zero.context, context)
        self.assertEqual(events, [])
        self.assertEqual(
            tuple(result._state.operation_id for result in results),
            (
                "zencad.typed.union",
                "zencad.typed.intersect",
                "zencad.typed.intersect",
                "zencad.typed.difference",
                "zencad.typed.section",
            ),
        )

    def test_sequence_and_variadic_booleans_across_policy_matrix(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    left = context.call(typed.box, 2)
                    right = context.call(typed.box, 2).translate(1, 0, 0)

                    results = (
                        context.call(typed.union, (left, right)),
                        context.call(typed.union, left, right),
                        context.call(typed.intersect, (left, right)),
                        context.call(typed.intersection, left, right),
                        context.call(typed.difference, (left, right)),
                        context.call(typed.difference, left, right),
                    )

                    self.assertTrue(all(type(result) is typed.Shape for result in results))
                    self.assertEqual(
                        tuple(round(float(result.mass()), 8) for result in results),
                        (12.0, 12.0, 4.0, 4.0, 4.0, 4.0),
                    )

    def test_boolean_sequences_preserve_order_and_singleton_identity(self):
        context = typed.Context.deferred(cache=False)
        base = context.call(typed.box, 3)
        first = context.call(typed.box, 1).translate(0, 0, 1)
        second = context.call(typed.box, 1).translate(2, 2, 1)

        reduced = context.call(typed.difference, (base, first, second))
        chained = base - first - second

        self.assertAlmostEqual(float(reduced.mass()), float(chained.mass()))
        self.assertAlmostEqual(float(context.call(typed.union, (base,)).mass()), 27.0)

    def test_boolean_operands_are_validated_before_graph_construction(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 1)

        with self.assertRaisesRegex(ValueError, "at least one Shape"):
            context.call(typed.union, ())
        with self.assertRaisesRegex(TypeError, "only Shape"):
            context.call(typed.intersect, (shape, object()))  # type: ignore[list-item]
        with self.assertRaisesRegex(TypeError, "sequence with extra"):
            context.call(typed.difference, (shape,), shape)
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.union, shape, other.call(typed.box, 1))


class TypedSectionTest(unittest.TestCase):
    def test_shape_and_plane_sections_return_general_shapes(self):
        context = typed.Context.deferred(cache=False)
        solid = context.call(typed.box, 2)

        by_shape = context.call(typed.section, solid, context.call(typed.sphere, 1.5))
        by_height = context.call(typed.section, solid, 1)
        by_vector = context.call(typed.section, solid, context.call(typed.vector3, 0, 0, 1))

        for result in (by_shape, by_height, by_vector):
            self.assertIs(type(result), typed.Shape)
            self.assertFalse(result.native().IsNull())
            self.assertGreater(len(result.edges()), 0)

    def test_section_rejects_invalid_plane_and_cross_context_shape(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "three coordinates"):
            context.call(typed.section, context.call(typed.box, 1), (0, 1))
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.section, context.call(typed.box, 1), other.call(typed.box, 1))


class TypedOperationCompatibilityTest(unittest.TestCase):
    def test_modeling_family_is_declared_at_module_level(self):
        for name in (
            "fillet",
            "chamfer",
            "fillet2d",
            "chamfer2d",
            "offset",
            "thicksolid",
            "shapefix_solid",
            "unify",
            "near_vertex",
            "near_edge",
            "near_wire",
            "near_face",
            "near_shell",
            "near_solid",
            "near_compsolid",
            "near_compound",
            "boundbox",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        context = typed.Context.deferred(cache=False)
        solid = context.call(typed.box, 4)
        face = context.call(typed.rectangle, 4, 4)
        point = context.call(typed.point3, 0.1, 0.1, 5)
        edge = context.call(typed.segment, context.call(typed.point3, ), context.call(typed.point3, 1, 0, 0))
        with using_context(context):
            values = (
                typed.fillet(solid, 0.1),
                typed.chamfer(solid, 0.1),
                typed.fillet2d(face, 0.1),
                typed.chamfer2d(face, 0.1),
                typed.offset(solid, 0.1),
                typed.thicksolid(solid, -0.1, (context.call(typed.point3, 2, 2, 4),)),
                typed.shapefix_solid(solid),
                typed.unify(solid),
                typed.near_vertex(solid, point),
                typed.near_edge(solid, point),
                typed.near_wire(solid, point),
                typed.near_face(solid, point),
                typed.near_shell(solid, point),
                typed.near_solid(solid, point),
                typed.boundbox(solid),
            )
            projection = typed.project(point, edge)

        self.assertTrue(all(value.context is context for value in values))
        self.assertIs(projection.point.context, context)
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.shape.fillet",
                "zencad.typed.shape.chamfer",
                "zencad.typed.shape.fillet2d",
                "zencad.typed.shape.chamfer2d",
                "zencad.typed.shape.offset",
                "zencad.typed.solid.thicksolid",
                "zencad.typed.solid.shapefix",
                "zencad.typed.shape.unify",
                "zencad.typed.shape.near_vertex",
                "zencad.typed.shape.near_edge",
                "zencad.typed.shape.near_wire",
                "zencad.typed.shape.near_face",
                "zencad.typed.shape.near_shell",
                "zencad.typed.shape.near_solid",
                "zencad.typed.shape.boundbox",
            ),
        )

    def test_root_style_fillet_wrappers_preserve_typed_results(self):
        context = typed.Context.deferred(cache=False)
        solid = context.call(typed.box, 3)
        face = context.call(typed.rectangle, 3, 3)

        self.assertIs(type(context.call(typed.fillet, solid, 0.1)), typed.Shape)
        self.assertIs(type(context.call(typed.chamfer, solid, 0.1)), typed.Shape)
        self.assertIs(type(context.call(typed.fillet2d, face, 0.1)), typed.Face)

    def test_restore_shapetype_returns_the_precise_handle_when_unique(self):
        context = typed.Context.deferred(cache=False)
        solid_as_shape = context.call(typed.union, (context.call(typed.box, 1),))
        face_as_shape = context.call(typed.section, context.call(typed.box, 1), 0.5)

        self.assertIs(type(solid_as_shape), typed.Shape)
        self.assertIs(type(solid_as_shape.restore_shapetype()), typed.Solid)
        self.assertIs(type(face_as_shape.restore_shapetype()), typed.Shape)

    def test_mesh_operations_return_immutable_rows(self):
        context = typed.Context.deferred(cache=False)
        mesh = context.call(typed.to_mesh, context.call(typed.box, 1), 0.1)
        face_mesh = context.call(
            typed.triangulate,
            context.call(typed.rectangle, 1, 1),
            0.1,
        )

        self.assertIs(type(mesh), typed.MeshData)
        self.assertIs(type(face_mesh), typed.MeshData)
        self.assertEqual(context.call(typed.get_nodes, mesh), mesh.positions)
        self.assertEqual(context.call(typed.get_triangles, mesh), mesh.triangles)
        self.assertEqual(mesh.get_nodes(), mesh.positions)
        self.assertEqual(mesh.get_triangles(), mesh.triangles)

        native = mesh.native()
        self.assertEqual(context.call(typed.get_nodes, native), mesh.positions)
        self.assertEqual(context.call(typed.get_triangles, native), mesh.triangles)


class TypedOffsetSewUnifyTest(unittest.TestCase):
    def test_sew_returns_precise_wire_and_shell_handles(self):
        context = typed.Context.deferred(cache=False)
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, 1, 0, 0),
            context.call(typed.point3, 1, 1, 0),
        )
        edges = (
            context.call(typed.segment, points[1], points[2]),
            context.call(typed.segment, points[0], points[1]),
        )
        wire = context.call(typed.sew, edges)
        shell = context.call(typed.sew, (context.call(typed.box, 1).faces()[0],))

        self.assertIs(type(wire), typed.Wire)
        self.assertEqual(len(wire.edges()), 2)
        self.assertIs(type(shell), typed.Shell)
        self.assertEqual(len(shell.faces()), 1)

    def test_offset_thicksolid_shapefix_and_unify(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    solid = context.call(typed.box, 4)

                    offset = context.call(typed.offset, solid, 0.25)
                    thick = context.call(typed.thicksolid,
                        solid,
                        -0.25,
                        (context.call(typed.point3, 2, 2, 4),),
                    )
                    fixed = context.call(typed.shapefix_solid, solid)
                    unified = context.call(typed.unify, solid)

                    self.assertIs(type(offset), typed.Shape)
                    self.assertGreater(float(offset.mass()), float(solid.mass()))
                    self.assertIs(type(thick), typed.Solid)
                    self.assertGreater(float(thick.mass()), 0)
                    self.assertIs(type(fixed), typed.Solid)
                    self.assertAlmostEqual(float(fixed.mass()), float(solid.mass()))
                    self.assertIs(type(unified), typed.Solid)
                    self.assertAlmostEqual(
                        float(unified.mass()),
                        float(solid.mass()),
                    )

    def test_modeling_boundaries_reject_mixed_or_wrong_context_inputs(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "at least one"):
            context.call(typed.sew, ())
        with self.assertRaisesRegex(TypeError, "all be"):
            context.call(typed.sew,   # type: ignore[arg-type]
                (
                    context.call(typed.segment, context.call(typed.point3, ), context.call(typed.point3, 1, 0, 0)),
                    context.call(typed.rectangle, 1, 1),
                )
            )
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.sew, (other.call(typed.rectangle, 1, 1),))
        with self.assertRaisesRegex(TypeError, "expects Solid"):
            context.call(typed.thicksolid, context.call(typed.rectangle, 1, 1), 0.1, ())  # type: ignore[arg-type]


class TypedGeometryQueriesTest(unittest.TestCase):
    def test_nearest_topology_queries_have_precise_handles_across_policies(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    shape = context.call(typed.box, 1)
                    point = context.call(typed.point3, 0.1, 0.1, 2)
                    results = (
                        context.call(typed.near_vertex, shape, point),
                        context.call(typed.near_edge, shape, point),
                        context.call(typed.near_wire, shape, point),
                        context.call(typed.near_face, shape, point),
                        context.call(typed.near_shell, shape, point),
                        context.call(typed.near_solid, shape, point),
                    )

                    self.assertEqual(
                        tuple(type(result) for result in results),
                        (
                            typed.Vertex,
                            typed.Edge,
                            typed.Wire,
                            typed.Face,
                            typed.Shell,
                            typed.Solid,
                        ),
                    )
                    self.assertEqual(results[0].point().value(), (0.0, 0.0, 1.0))
                    self.assertTrue(all(not result.native().IsNull() for result in results))

    def test_missing_nearest_topology_has_an_actionable_error(self):
        context = typed.Context.deferred(cache=False)
        with self.assertRaisesRegex(ValueError, "no compound topology"):
            context.call(typed.near_compound, context.call(typed.box, 1), context.call(typed.point3, )).native()

    def test_curve_projection_is_a_structured_typed_result(self):
        context = typed.Context.deferred(cache=False)
        edge = context.call(typed.segment,
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, 10, 0, 0),
        )
        projection = context.call(typed.project, context.call(typed.point3, 3, 4, 0), edge)

        self.assertIs(type(projection), typed.CurveProjection)
        self.assertEqual(projection.point.value(), (3.0, 0.0, 0.0))
        self.assertAlmostEqual(float(projection.parameter), 3.0)
        self.assertAlmostEqual(float(projection.distance), 4.0)
        self.assertEqual(projection.value(), ((3.0, 0.0, 0.0), 3.0, 4.0))
    def test_geometry_queries_reject_wrong_domain_or_context(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 1)

        with self.assertRaisesRegex(TypeError, "expects Point3"):
            shape.near_vertex((0, 0, 0))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.near_face, shape, other.call(typed.point3, ))
        with self.assertRaisesRegex(TypeError, "Curve or Edge"):
            context.call(typed.project, context.call(typed.point3, ), shape)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
