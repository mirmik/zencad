import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
import numpy
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID

from zencad import geom as typed
from zencad.operation import DomainOperation, using_context


def _tetrahedron_data(
    context: typed.Context,
) -> tuple[tuple[typed.Point3, ...], tuple[tuple[int, ...], ...]]:
    return (
        (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, 1, 0, 0),
            context.call(typed.point3, 0, 1, 0),
            context.call(typed.point3, 0, 0, 1),
        ),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )


class TypedShellConstructorsTest(unittest.TestCase):
    def test_shell_family_is_declared_at_module_level(self):
        for name in (
            "make_shell",
            "fill3d",
            "polyhedron_shell",
            "convex_hull_shape",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        points, faces = _tetrahedron_data(context)
        with using_context(context):
            shell = typed.make_shell(typed.polygon(points[:3]))
            solid = typed.fill3d(typed.polyhedron_shell(points, faces))
            polyhedron = typed.polyhedron(points, faces)
            hull = typed.convex_hull_shape(points, shell=True)
            tetrahedron = typed.tetrahedron()
            cube = typed.hexahedron(shell=True)
            octahedron = typed.octahedron()
            dodecahedron = typed.dodecahedron(shell=True)
            icosahedron = typed.icosahedron()
            platonic = typed.platonic(6)

        values = (
            shell,
            solid,
            polyhedron,
            hull,
            tetrahedron,
            cube,
            octahedron,
            dodecahedron,
            icosahedron,
            platonic,
        )
        self.assertTrue(all(value.context is context for value in values))
        self.assertEqual(events, [])
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.make_shell",
                "zencad.typed.fill3d",
                "zencad.typed.fill3d",
                "zencad.typed.convex_hull_shape",
                "zencad.typed.fill3d",
                "zencad.typed.polyhedron_shell",
                "zencad.typed.fill3d",
                "zencad.typed.polyhedron_shell",
                "zencad.typed.fill3d",
                "zencad.typed.fill3d",
            ),
        )

    def test_shell_and_platonic_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    points, faces = _tetrahedron_data(context)
                    values = (
                        context.call(
                            typed.make_shell, context.call(typed.polygon, points[:3])
                        ),
                        context.call(typed.polyhedron_shell, points, faces),
                        context.call(typed.polyhedron, points, faces),
                        context.call(typed.polyhedron, points, faces, shell=True),
                        context.call(typed.convex_hull_shape, points),
                        context.call(typed.convex_hull_shape, points, shell=True),
                        context.call(
                            typed.tetrahedron,
                        ),
                        context.call(typed.hexahedron, shell=True),
                        context.call(
                            typed.octahedron,
                        ),
                        context.call(typed.dodecahedron, shell=True),
                        context.call(
                            typed.icosahedron,
                        ),
                        context.call(typed.platonic, 6),
                        context.call(typed.platonic, 20, shell=True),
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
        context = typed.Context.deferred(cache=False)
        points, faces = _tetrahedron_data(context)
        shell = context.call(typed.polyhedron_shell, points, faces)
        solid = context.call(typed.fill3d, shell)
        cube = context.call(typed.hexahedron, a=2)
        platonic = (
            context.call(
                typed.tetrahedron,
            ),
            context.call(
                typed.hexahedron,
            ),
            context.call(
                typed.octahedron,
            ),
            context.call(
                typed.dodecahedron,
            ),
            context.call(
                typed.icosahedron,
            ),
        )

        self.assertEqual(len(shell.faces()), 4)
        self.assertAlmostEqual(float(shell.mass()), 1 / 6)
        self.assertAlmostEqual(float(solid.mass()), 1 / 6)
        self.assertAlmostEqual(float(cube.mass()), 8)
        self.assertEqual(
            tuple(len(shape.faces()) for shape in platonic), (4, 6, 8, 12, 20)
        )
        self.assertTrue(all(float(shape.mass()) > 0 for shape in platonic))

    def test_polyhedron_accepts_numpy_mesh_arrays(self):
        vertices = numpy.asarray(
            ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
            dtype=numpy.float64,
        )
        faces = numpy.asarray(
            ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
            dtype=numpy.int64,
        )

        solid = typed.polyhedron(vertices, faces)

        self.assertIs(type(solid), typed.Solid)
        self.assertAlmostEqual(float(solid.mass()), 1 / 6)

    def test_convex_hull_faces_are_an_explicit_materialization_boundary(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        unit = context.call(typed.box, 1).mass()
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, unit, 0, 0),
            context.call(typed.point3, 0, unit, 0),
            context.call(typed.point3, 0, 0, unit),
        )

        self.assertEqual(events, [])
        faces = context.call(typed.convex_hull, points, qhull_options="Qt")
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
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        unit = context.call(typed.box, 2).mass() / 8
        points = (
            context.call(typed.point3, 0, 0, 0),
            context.call(typed.point3, unit, 0, 0),
            context.call(typed.point3, 0, unit, 0),
            context.call(typed.point3, 0, 0, unit),
        )
        faces = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))
        polyhedron = context.call(typed.polyhedron, points, faces)
        platonic = context.call(typed.tetrahedron, r=unit)
        hull = context.call(typed.convex_hull_shape, points)

        self.assertEqual(events, [])
        self.assertTrue(
            all(not shape.native().IsNull() for shape in (polyhedron, platonic, hull))
        )
        self.assertTrue(events)

    def test_shell_artifacts_restore_from_shared_cache(self):
        store = MemoryCacheStore()

        def values(context: typed.Context) -> tuple[typed.Shape, ...]:
            points, faces = _tetrahedron_data(context)
            return (
                context.call(typed.polyhedron_shell, points, faces),
                context.call(typed.polyhedron, points, faces),
                context.call(typed.convex_hull_shape, points, shell=True),
                context.call(
                    typed.tetrahedron,
                ),
            )

        first_events = []
        first = typed.Context.deferred(
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
        second = typed.Context.deferred(
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
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        points, faces = _tetrahedron_data(context)

        with self.assertRaisesRegex(ValueError, "at least one Face"):
            context.call(typed.make_shell, ()).native()
        with self.assertRaises(TypeError):
            context.call(typed.make_shell, (context.call(typed.box, 1),)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.make_shell, other.call(typed.box, 1).faces()[0])
        with self.assertRaises(TypeError):
            context.call(typed.fill3d, context.call(typed.box, 1)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(IndexError, "outside"):
            context.call(typed.polyhedron, points, ((0, 1, 9),)).native()
        with self.assertRaisesRegex(ValueError, "at least three"):
            context.call(typed.polyhedron, points, ((0, 1),)).native()
        with self.assertRaisesRegex(TypeError, "qhull_options"):
            context.call(typed.convex_hull, points, qhull_options=3)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "one of"):
            context.call(typed.platonic, 5)
        with self.assertRaisesRegex(TypeError, "nfaces must be int"):
            context.call(typed.platonic, True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "shell must be bool"):
            context.call(typed.tetrahedron, shell="yes")  # type: ignore[arg-type]
        self.assertIs(type(context.call(typed.polyhedron, points, faces)), typed.Solid)


if __name__ == "__main__":
    unittest.main()
