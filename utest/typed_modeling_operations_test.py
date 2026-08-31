import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore

from zencad import _typed as typed


class TypedBooleanOperationsTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
