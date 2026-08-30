import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID

from zencad import _typed as typed


def _tetrahedron_data(
    runtime: typed.Runtime,
) -> tuple[tuple[typed.Point3, ...], tuple[tuple[int, ...], ...]]:
    return (
        (
            runtime.point3(0, 0, 0),
            runtime.point3(1, 0, 0),
            runtime.point3(0, 1, 0),
            runtime.point3(0, 0, 1),
        ),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )


class TypedShellConstructorsTest(unittest.TestCase):
    def test_shell_and_platonic_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    points, faces = _tetrahedron_data(runtime)
                    values = (
                        runtime.make_shell(runtime.polygon(points[:3])),
                        runtime.polyhedron_shell(points, faces),
                        runtime.polyhedron(points, faces),
                        runtime.polyhedron(points, faces, shell=True),
                        runtime.convex_hull_shape(points),
                        runtime.convex_hull_shape(points, shell=True),
                        runtime.tetrahedron(),
                        runtime.hexahedron(shell=True),
                        runtime.octahedron(),
                        runtime.dodecahedron(shell=True),
                        runtime.icosahedron(),
                        runtime.platonic(6),
                        runtime.platonic(20, shell=True),
                    )
                    policy_types = tuple(type(value) for value in values)
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Shell,
                            typed.Shell,
                            typed.Solid,
                            typed.Shell,
                            typed.Solid,
                            typed.Shell,
                            typed.Solid,
                            typed.Shell,
                            typed.Solid,
                            typed.Shell,
                            typed.Solid,
                            typed.Solid,
                            typed.Shell,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    natives = tuple(value.native() for value in values)
                    self.assertTrue(all(not native.IsNull() for native in natives))
                    shell_indices = {0, 1, 3, 5, 7, 9, 12}
                    self.assertTrue(
                        all(
                            native.ShapeType()
                            == (
                                TopAbs_SHELL if index in shell_indices else TopAbs_SOLID
                            )
                            for index, native in enumerate(natives)
                        )
                    )

        self.assertEqual(len(observed_types), 1)

    def test_polyhedra_and_platonic_geometry_is_truthful(self):
        runtime = typed.Runtime.deferred(cache=False)
        points, faces = _tetrahedron_data(runtime)
        shell = runtime.polyhedron_shell(points, faces)
        solid = runtime.fill3d(shell)
        cube = runtime.hexahedron(a=2)
        platonic = (
            runtime.tetrahedron(),
            runtime.hexahedron(),
            runtime.octahedron(),
            runtime.dodecahedron(),
            runtime.icosahedron(),
        )

        self.assertEqual(len(shell.faces()), 4)
        self.assertAlmostEqual(float(shell.mass()), 1 / 6)
        self.assertAlmostEqual(float(solid.mass()), 1 / 6)
        self.assertAlmostEqual(float(cube.mass()), 8)
        self.assertEqual(
            tuple(len(shape.faces()) for shape in platonic), (4, 6, 8, 12, 20)
        )
        self.assertTrue(all(float(shape.mass()) > 0 for shape in platonic))

    def test_convex_hull_faces_are_an_explicit_materialization_boundary(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        unit = runtime.box(1).mass()
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(unit, 0, 0),
            runtime.point3(0, unit, 0),
            runtime.point3(0, 0, unit),
        )

        self.assertEqual(events, [])
        faces = runtime.convex_hull(points, qhull_options="Qt")
        self.assertTrue(events)
        self.assertIs(type(faces), tuple)
        self.assertEqual(len(faces), 4)
        self.assertTrue(
            all(
                type(face) is tuple
                and len(face) == 3
                and all(type(index) is int for index in face)
                for face in faces
            )
        )

    def test_graph_points_and_scalars_remain_deferred_for_shapes(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        unit = runtime.box(2).mass() / 8
        points = (
            runtime.point3(0, 0, 0),
            runtime.point3(unit, 0, 0),
            runtime.point3(0, unit, 0),
            runtime.point3(0, 0, unit),
        )
        faces = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))
        polyhedron = runtime.polyhedron(points, faces)
        platonic = runtime.tetrahedron(r=unit)
        hull = runtime.convex_hull_shape(points)

        self.assertEqual(events, [])
        self.assertTrue(
            all(not shape.native().IsNull() for shape in (polyhedron, platonic, hull))
        )
        self.assertTrue(events)

    def test_shell_artifacts_restore_from_shared_cache(self):
        store = MemoryCacheStore()

        def values(runtime: typed.Runtime) -> tuple[typed.Shape, ...]:
            points, faces = _tetrahedron_data(runtime)
            return (
                runtime.polyhedron_shell(points, faces),
                runtime.polyhedron(points, faces),
                runtime.convex_hull_shape(points, shell=True),
                runtime.tetrahedron(),
            )

        first_events = []
        first = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        for value in values(first):
            self.assertFalse(value.native().IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        for value in values(second):
            self.assertFalse(value.native().IsNull())
        hits = {
            event.operation_id
            for event in second_events
            if event.kind is EvaluationEventKind.CACHE_HIT
        }
        self.assertTrue(
            {
                "zencad.typed.polyhedron_shell",
                "zencad.typed.fill3d",
                "zencad.typed.convex_hull_shape",
            }.issubset(hits)
        )

    def test_invalid_inputs_fail_at_the_typed_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        points, faces = _tetrahedron_data(runtime)

        with self.assertRaisesRegex(ValueError, "at least one Face"):
            runtime.make_shell(())
        with self.assertRaisesRegex(TypeError, "only Face"):
            runtime.make_shell((runtime.box(1),))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.make_shell(other.box(1).faces()[0])
        with self.assertRaisesRegex(TypeError, "fill3d expects Shell"):
            runtime.fill3d(runtime.box(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(IndexError, "outside"):
            runtime.polyhedron(points, ((0, 1, 9),))
        with self.assertRaisesRegex(ValueError, "at least three"):
            runtime.polyhedron(points, ((0, 1),))
        with self.assertRaisesRegex(TypeError, "qhull_options"):
            runtime.convex_hull(points, qhull_options=3)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "one of"):
            runtime.platonic(5)
        with self.assertRaisesRegex(TypeError, "nfaces must be int"):
            runtime.platonic(True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "shell must be bool"):
            runtime.tetrahedron(shell="yes")  # type: ignore[arg-type]
        self.assertIs(type(runtime.polyhedron(points, faces)), typed.Solid)


if __name__ == "__main__":
    unittest.main()
