from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.Poly import Poly_Triangulation

from zencad import _typed as typed
from zencad.operation import using_context


class TypedBrepBoundaryTest(unittest.TestCase):
    def test_module_conversion_boundaries_match_context(self):
        context = typed.Context.deferred(cache=False)
        source = context.call(typed.box, 2)
        svg_source = context.call(typed.rectangle, 2, 3)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            brep_path = root / "module.brep"
            stl_path = root / "module.stl"
            svg_path = root / "module.svg"

            typed.to_brep(source, brep_path)
            self.assertTrue(typed.to_stl(source, stl_path, 0.1))
            svg = typed.to_svg_string(svg_source)
            typed.to_svg(svg_source, svg_path)
            with using_context(context):
                from_brep = typed.from_brep(brep_path)
                from_svg_string = typed.from_svg_string(svg)
                from_svg = typed.from_svg(svg_path)

            self.assertIs(type(from_brep), typed.Shape)
            self.assertIs(from_brep.context, context)
            self.assertIs(from_svg_string.context, context)
            self.assertIs(from_svg.context, context)
            self.assertGreater(from_brep.mass().value(), 0)
            self.assertGreater(len(from_svg.edges()), 0)
            self.assertGreater(stl_path.stat().st_size, 0)

    def test_brep_round_trip_across_context_policies(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
                for cache in (False, True):
                    with self.subTest(mode=mode, cache=cache):
                        context = typed.Context(
                            mode=mode,
                            cache=cache,
                            cache_store=MemoryCacheStore(),
                        )
                        source = context.call(typed.box, 2) - context.call(typed.sphere, 0.5)
                        path = root / f"shape-{mode.value}-{cache}.brep"

                        self.assertIsNone(context.call(typed.to_brep, source, path))
                        restored = context.call(typed.from_brep, path)

                        self.assertIs(type(restored), typed.Shape)
                        self.assertAlmostEqual(
                            float(restored.mass()),
                            float(source.mass()),
                        )
                        self.assertGreater(path.stat().st_size, 0)

    def test_brep_errors_name_the_failed_path(self):
        context = typed.Context.deferred(cache=False)
        with TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing.brep"
            with self.assertRaisesRegex(OSError, "Failed to read BREP"):
                context.call(typed.from_brep, missing)


class TypedStlSvgBoundaryTest(unittest.TestCase):
    def test_stl_and_svg_exports_use_explicit_owned_snapshots(self):
        context = typed.Context.deferred(cache=False)
        source = context.call(typed.rectangle, 4, 3)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            stl_path = root / "shape.stl"
            svg_path = root / "shape.svg"

            self.assertTrue(context.call(typed.to_stl, context.call(typed.box, 1), stl_path, 0.1))
            svg = context.call(typed.to_svg_string, source)
            self.assertIs(type(svg), str)
            self.assertIn("<svg", svg)
            self.assertIsNone(context.call(typed.to_svg, source, svg_path))

            from_string = context.call(typed.from_svg_string, svg)
            from_file = context.call(typed.from_svg, svg_path)
            self.assertIs(type(from_string), typed.Shape)
            self.assertIs(type(from_file), typed.Shape)
            self.assertEqual(len(from_string.edges()), 4)
            self.assertEqual(len(from_file.edges()), 4)
            self.assertGreater(stl_path.stat().st_size, 0)
            self.assertGreater(svg_path.stat().st_size, 0)

    def test_convert_inputs_are_validated_at_the_typed_boundary(self):
        context = typed.Context.deferred(cache=False)
        with self.assertRaisesRegex(ValueError, "deflection"):
            context.call(typed.to_stl, context.call(typed.box, 1), "unused.stl", 0)
        with self.assertRaisesRegex(TypeError, "expects str"):
            context.call(typed.from_svg_string, b"<svg/>")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "mapping must be bool"):
            context.call(typed.to_svg_string, context.call(typed.rectangle, 1, 1), mapping=1)  # type: ignore[arg-type]


class TypedMeshCompatibilityBoundaryTest(unittest.TestCase):
    def test_mesh_native_aliases_return_fresh_triangulations(self):
        context = typed.Context.deferred(cache=False)
        mesh = context.call(typed.box, 1).to_mesh()

        first = context.call(typed.mesh_to_poly_triangulation, mesh)
        second = mesh.mesh_to_poly_triangulation()

        self.assertIs(type(first), Poly_Triangulation)
        self.assertIs(type(second), Poly_Triangulation)
        self.assertIsNot(first, second)
        self.assertEqual(first.NbNodes(), mesh.vertex_count)
        self.assertEqual(first.NbTriangles(), mesh.triangle_count)

    def test_mesh_adapter_rejects_wrong_domain_and_context(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "expects MeshData"):
            context.call(typed.mesh_to_poly_triangulation, context.call(typed.box, 1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.mesh_to_poly_triangulation, other.call(typed.box, 1).to_mesh())


if __name__ == "__main__":
    unittest.main()
