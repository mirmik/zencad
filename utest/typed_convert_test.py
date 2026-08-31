from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.Poly import Poly_Triangulation

from zencad import _typed as typed


class TypedBrepBoundaryTest(unittest.TestCase):
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
