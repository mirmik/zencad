import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_runtime


class TypedBooleanOperationsTest(unittest.TestCase):
    def test_boolean_family_is_declared_at_module_level(self):
        for name in ("empty_shape", "union", "intersect", "difference", "section"):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        left = runtime.box(2)
        right = runtime.box(2).translate(1, 0, 0)
        results = (
            typed.union(left, right),
            typed.intersect((left, right)),
            typed.intersection(left, right),
            typed.difference(left, right),
            typed.section(left, 1),
        )
        with using_runtime(runtime):
            zero = typed.empty_shape()
            legacy_zero = typed.nullshape()

        self.assertTrue(all(result.runtime is runtime for result in results))
        self.assertIs(zero.runtime, runtime)
        self.assertIs(legacy_zero.runtime, runtime)
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
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    left = runtime.box(2)
                    right = runtime.box(2).translate(1, 0, 0)

                    results = (
                        runtime.union((left, right)),
                        runtime.union(left, right),
                        runtime.intersect((left, right)),
                        runtime.intersection(left, right),
                        runtime.difference((left, right)),
                        runtime.difference(left, right),
                    )

                    self.assertTrue(all(type(result) is typed.Shape for result in results))
                    self.assertEqual(
                        tuple(round(float(result.mass()), 8) for result in results),
                        (12.0, 12.0, 4.0, 4.0, 4.0, 4.0),
                    )

    def test_boolean_sequences_preserve_order_and_singleton_identity(self):
        runtime = typed.Runtime.deferred(cache=False)
        base = runtime.box(3)
        first = runtime.box(1).translate(0, 0, 1)
        second = runtime.box(1).translate(2, 2, 1)

        reduced = runtime.difference((base, first, second))
        chained = base - first - second

        self.assertAlmostEqual(float(reduced.mass()), float(chained.mass()))
        self.assertAlmostEqual(float(runtime.union((base,)).mass()), 27.0)

    def test_boolean_operands_are_validated_before_graph_construction(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        shape = runtime.box(1)

        with self.assertRaisesRegex(ValueError, "at least one Shape"):
            runtime.union(())
        with self.assertRaisesRegex(TypeError, "only Shape"):
            runtime.intersect((shape, object()))  # type: ignore[list-item]
        with self.assertRaisesRegex(TypeError, "sequence with extra"):
            runtime.difference((shape,), shape)
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.union(shape, other.box(1))


class TypedSectionTest(unittest.TestCase):
    def test_shape_and_plane_sections_return_general_shapes(self):
        runtime = typed.Runtime.deferred(cache=False)
        solid = runtime.box(2)

        by_shape = runtime.section(solid, runtime.sphere(1.5))
        by_height = runtime.section(solid, 1)
        by_vector = runtime.section(solid, runtime.vector3(0, 0, 1))

        for result in (by_shape, by_height, by_vector):
            self.assertIs(type(result), typed.Shape)
            self.assertFalse(result.native().IsNull())
            self.assertGreater(len(result.edges()), 0)

    def test_section_rejects_invalid_plane_and_cross_runtime_shape(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "three coordinates"):
            runtime.section(runtime.box(1), (0, 1))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.section(runtime.box(1), other.box(1))


class TypedOperationCompatibilityTest(unittest.TestCase):
    def test_root_style_fillet_wrappers_preserve_typed_results(self):
        runtime = typed.Runtime.deferred(cache=False)
        solid = runtime.box(3)
        face = runtime.rectangle(3, 3)

        self.assertIs(type(runtime.fillet(solid, 0.1)), typed.Shape)
        self.assertIs(type(runtime.chamfer(solid, 0.1)), typed.Shape)
        self.assertIs(type(runtime.fillet2d(face, 0.1)), typed.Face)

    def test_restore_shapetype_returns_the_precise_handle_when_unique(self):
        runtime = typed.Runtime.deferred(cache=False)
        solid_as_shape = runtime.union((runtime.box(1),))
        face_as_shape = runtime.section(runtime.box(1), 0.5)

        self.assertIs(type(solid_as_shape), typed.Shape)
        self.assertIs(type(solid_as_shape.restore_shapetype()), typed.Solid)
        self.assertIs(type(face_as_shape.restore_shapetype()), typed.Shape)

    def test_triangulation_compatibility_returns_immutable_rows(self):
        runtime = typed.Runtime.deferred(cache=False)
        mesh = runtime.triangulate(runtime.box(1), 0.1)
        face_mesh = runtime.triangulate_face(runtime.rectangle(1, 1), 0.1)

        self.assertIs(type(mesh), typed.MeshData)
        self.assertIs(type(face_mesh), typed.MeshData)
        self.assertEqual(runtime.get_nodes(mesh), mesh.positions)
        self.assertEqual(runtime.get_triangles(mesh), mesh.triangles)
        self.assertEqual(mesh.get_nodes(), mesh.positions)
        self.assertEqual(mesh.get_triangles(), mesh.triangles)

        native = mesh.native()
        self.assertEqual(runtime.get_nodes(native), mesh.positions)
        self.assertEqual(runtime.get_triangles(native), mesh.triangles)


class TypedOffsetSewUnifyTest(unittest.TestCase):
    def test_sew_returns_precise_wire_and_shell_handles(self):
        runtime = typed.Runtime.deferred(cache=False)
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(1, 0, 0),
            runtime.point3(1, 1, 0),
        )
        edges = (
            runtime.segment(points[1], points[2]),
            runtime.segment(points[0], points[1]),
        )
        wire = runtime.sew(edges)
        shell = runtime.sew((runtime.box(1).faces()[0],))

        self.assertIs(type(wire), typed.Wire)
        self.assertEqual(len(wire.edges()), 2)
        self.assertIs(type(shell), typed.Shell)
        self.assertEqual(len(shell.faces()), 1)

    def test_offset_thicksolid_shapefix_and_unify(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    solid = runtime.box(4)

                    offset = runtime.offset(solid, 0.25)
                    thick = runtime.thicksolid(
                        solid,
                        -0.25,
                        (runtime.point3(2, 2, 4),),
                    )
                    fixed = runtime.shapefix_solid(solid)
                    unified = runtime.unify(solid)

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

    def test_modeling_boundaries_reject_mixed_or_wrong_runtime_inputs(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "at least one"):
            runtime.sew(())
        with self.assertRaisesRegex(TypeError, "all be"):
            runtime.sew(  # type: ignore[arg-type]
                (
                    runtime.segment(runtime.point3(), runtime.point3(1, 0, 0)),
                    runtime.rectangle(1, 1),
                )
            )
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.sew((other.rectangle(1, 1),))
        with self.assertRaisesRegex(TypeError, "expects Solid"):
            runtime.thicksolid(runtime.rectangle(1, 1), 0.1, ())  # type: ignore[arg-type]


class TypedGeometryQueriesTest(unittest.TestCase):
    def test_nearest_topology_queries_have_precise_handles_across_policies(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    shape = runtime.box(1)
                    point = runtime.point3(0.1, 0.1, 2)
                    results = (
                        runtime.near_vertex(shape, point),
                        runtime.near_edge(shape, point),
                        runtime.near_wire(shape, point),
                        runtime.near_face(shape, point),
                        runtime.near_shell(shape, point),
                        runtime.near_solid(shape, point),
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
        runtime = typed.Runtime.deferred(cache=False)
        with self.assertRaisesRegex(ValueError, "no compound topology"):
            runtime.near_compound(runtime.box(1), runtime.point3()).native()

    def test_curve_projection_is_a_structured_typed_result(self):
        runtime = typed.Runtime.deferred(cache=False)
        edge = runtime.segment(
            runtime.point3(0, 0, 0),
            runtime.point3(10, 0, 0),
        )
        projection = runtime.project(runtime.point3(3, 4, 0), edge)

        self.assertIs(type(projection), typed.CurveProjection)
        self.assertEqual(projection.point.value(), (3.0, 0.0, 0.0))
        self.assertAlmostEqual(float(projection.parameter), 3.0)
        self.assertAlmostEqual(float(projection.distance), 4.0)
        self.assertEqual(projection.value(), ((3.0, 0.0, 0.0), 3.0, 4.0))
        self.assertIs(projection.unlazy(), projection)

    def test_geometry_queries_reject_wrong_domain_or_runtime(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        shape = runtime.box(1)

        with self.assertRaisesRegex(TypeError, "expects Point3"):
            shape.near_vertex((0, 0, 0))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.near_face(shape, other.point3())
        with self.assertRaisesRegex(TypeError, "Curve or Edge"):
            runtime.project(runtime.point3(), shape)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
