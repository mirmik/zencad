from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.Poly import Poly_Triangulation

from zencad import _typed as typed
from zencad.operation import using_runtime


class TypedBrepBoundaryTest(unittest.TestCase):
    def test_module_conversion_boundaries_match_runtime(self):
        runtime = typed.Runtime.deferred(cache=False)
        source = runtime.box(2)
        svg_source = runtime.rectangle(2, 3)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            brep_path = root / "module.brep"
            stl_path = root / "module.stl"
            svg_path = root / "module.svg"

            typed.to_brep(source, brep_path)
            self.assertTrue(typed.to_stl(source, stl_path, 0.1))
            svg = typed.to_svg_string(svg_source)
            typed.to_svg(svg_source, svg_path)
            with using_runtime(runtime):
                from_brep = typed.from_brep(brep_path)
                from_svg_string = typed.from_svg_string(svg)
                from_svg = typed.from_svg(svg_path)

            self.assertIs(type(from_brep), typed.Shape)
            self.assertIs(from_brep.runtime, runtime)
            self.assertIs(from_svg_string.runtime, runtime)
            self.assertIs(from_svg.runtime, runtime)
            self.assertGreater(from_brep.mass().value(), 0)
            self.assertGreater(len(from_svg.edges()), 0)
            self.assertGreater(stl_path.stat().st_size, 0)

    def test_brep_round_trip_across_runtime_policies(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
                for cache in (False, True):
                    with self.subTest(mode=mode, cache=cache):
                        runtime = typed.Runtime(
                            mode=mode,
                            cache=cache,
                            cache_store=MemoryCacheStore(),
                        )
                        source = runtime.box(2) - runtime.sphere(0.5)
                        path = root / f"shape-{mode.value}-{cache}.brep"

                        self.assertIsNone(runtime.to_brep(source, path))
                        restored = runtime.from_brep(path)

                        self.assertIs(type(restored), typed.Shape)
                        self.assertAlmostEqual(
                            float(restored.mass()),
                            float(source.mass()),
                        )
                        self.assertGreater(path.stat().st_size, 0)

    def test_brep_errors_name_the_failed_path(self):
        runtime = typed.Runtime.deferred(cache=False)
        with TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing.brep"
            with self.assertRaisesRegex(OSError, "Failed to read BREP"):
                runtime.from_brep(missing)


class TypedStlSvgBoundaryTest(unittest.TestCase):
    def test_stl_and_svg_exports_use_explicit_owned_snapshots(self):
        runtime = typed.Runtime.deferred(cache=False)
        source = runtime.rectangle(4, 3)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            stl_path = root / "shape.stl"
            svg_path = root / "shape.svg"

            self.assertTrue(runtime.to_stl(runtime.box(1), stl_path, 0.1))
            svg = runtime.to_svg_string(source)
            self.assertIs(type(svg), str)
            self.assertIn("<svg", svg)
            self.assertIsNone(runtime.to_svg(source, svg_path))

            from_string = runtime.from_svg_string(svg)
            from_file = runtime.from_svg(svg_path)
            self.assertIs(type(from_string), typed.Shape)
            self.assertIs(type(from_file), typed.Shape)
            self.assertEqual(len(from_string.edges()), 4)
            self.assertEqual(len(from_file.edges()), 4)
            self.assertGreater(stl_path.stat().st_size, 0)
            self.assertGreater(svg_path.stat().st_size, 0)

    def test_convert_inputs_are_validated_at_the_typed_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        with self.assertRaisesRegex(ValueError, "deflection"):
            runtime.to_stl(runtime.box(1), "unused.stl", 0)
        with self.assertRaisesRegex(TypeError, "expects str"):
            runtime.from_svg_string(b"<svg/>")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "mapping must be bool"):
            runtime.to_svg_string(runtime.rectangle(1, 1), mapping=1)  # type: ignore[arg-type]


class TypedMeshCompatibilityBoundaryTest(unittest.TestCase):
    def test_mesh_native_aliases_return_fresh_triangulations(self):
        runtime = typed.Runtime.deferred(cache=False)
        mesh = runtime.box(1).to_mesh()

        first = runtime.mesh_to_poly_triangulation(mesh)
        second = mesh.mesh_to_poly_triangulation()

        self.assertIs(type(first), Poly_Triangulation)
        self.assertIs(type(second), Poly_Triangulation)
        self.assertIsNot(first, second)
        self.assertEqual(first.NbNodes(), mesh.vertex_count)
        self.assertEqual(first.NbTriangles(), mesh.triangle_count)

    def test_mesh_adapter_rejects_wrong_domain_and_runtime(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "expects MeshData"):
            runtime.mesh_to_poly_triangulation(runtime.box(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.mesh_to_poly_triangulation(other.box(1).to_mesh())


if __name__ == "__main__":
    unittest.main()
