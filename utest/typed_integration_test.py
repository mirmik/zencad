import unittest

import evalcache
from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore

from zencad import _typed as typed


class TypedDomainIntegrationTest(unittest.TestCase):
    def _chain(self, runtime: typed.Runtime):
        seed = runtime.box(2)
        offset = seed.mass() / 8
        shape = seed.translate(offset, 2, 3)
        edge = shape.edges()[0]
        face = shape.faces()[0]
        return (
            shape,
            edge,
            face,
            edge.curve(),
            face.surface(),
            shape.boundbox(),
            shape.to_mesh(),
        )

    def test_complete_shape_domain_chain_is_policy_independent(self):
        observed = set()

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
                    shape, edge, face, curve, surface, bounds, mesh = self._chain(
                        runtime
                    )
                    result_types = tuple(
                        type(value)
                        for value in (
                            shape,
                            edge,
                            face,
                            curve,
                            surface,
                            bounds,
                            mesh,
                        )
                    )
                    observed.add(result_types)
                    self.assertEqual(
                        result_types,
                        (
                            typed.Solid,
                            typed.Edge,
                            typed.Face,
                            typed.Curve,
                            typed.Surface,
                            typed.BoundaryBox,
                            typed.MeshData,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertEqual(curve.range().value(), (0.0, 2.0))
                    self.assertAlmostEqual(
                        curve.point(curve.range().lower).value()[0], 1.0
                    )
                    self.assertEqual(surface.u_range().length().value(), 2.0)
                    self.assertEqual(surface.v_range().length().value(), 2.0)
                    mesh_bounds = mesh.boundbox().value()
                    shape_bounds = bounds.value()
                    for actual, expected in zip(mesh_bounds.minimum, (1.0, 2.0, 3.0)):
                        self.assertAlmostEqual(actual, expected)
                    for actual, expected in zip(mesh_bounds.maximum, (3.0, 4.0, 5.0)):
                        self.assertAlmostEqual(actual, expected)
                    self.assertTrue(
                        all(
                            outer <= inner
                            for outer, inner in zip(
                                shape_bounds.minimum, mesh_bounds.minimum
                            )
                        )
                    )
                    self.assertTrue(
                        all(
                            outer >= inner
                            for outer, inner in zip(
                                shape_bounds.maximum, mesh_bounds.maximum
                            )
                        )
                    )
                    self.assertEqual(mesh.triangle_count, 12)
                    self.assertTrue(events)

        self.assertEqual(len(observed), 1)

    def test_no_domain_result_is_a_legacy_lazy_proxy(self):
        runtime = typed.Runtime.deferred(cache=False)
        shape, edge, face, curve, surface, bounds, mesh = self._chain(runtime)
        scalar = shape.mass()
        point = shape.center()
        vector = mesh.boundbox().size
        interval = curve.range()
        results = (
            shape,
            edge,
            face,
            curve,
            surface,
            bounds,
            mesh,
            scalar,
            point,
            vector,
            interval,
        )

        for result in results:
            with self.subTest(result_type=type(result).__name__):
                self.assertNotIsInstance(result, evalcache.LazyObject)
                self.assertNotIn("Lazy", type(result).__name__)

        materialized = (
            scalar.value(),
            point.value(),
            interval.value(),
            bounds.value(),
            mesh.value(),
        )
        for result in materialized:
            self.assertNotIsInstance(result, evalcache.LazyObject)

    def test_top_level_private_exports_are_complete_and_unique(self):
        expected = {
            "BoundaryBox",
            "BoundaryBoxRecord",
            "Curve",
            "Curve2",
            "Edge",
            "Face",
            "Interval",
            "MeshArrayRecord",
            "MeshData",
            "MeshDataRecord",
            "Point2",
            "Point3",
            "Runtime",
            "Scalar",
            "Shape",
            "Solid",
            "Surface",
            "Transform",
            "Vector2",
            "Vector3",
        }

        self.assertEqual(len(typed.__all__), len(set(typed.__all__)))
        self.assertTrue(expected <= set(typed.__all__))
        for name in typed.__all__:
            self.assertTrue(hasattr(typed, name), name)

    def test_fresh_runtime_reuses_every_cacheable_domain_family(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        _, _, _, curve, surface, bounds, mesh = self._chain(first)
        curve.native()
        surface.native()
        bounds.value()
        mesh.value()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        _, _, _, curve, surface, bounds, mesh = self._chain(second)
        curve.native()
        surface.native()
        bounds.value()
        mesh.value()

        hits = [
            event for event in events if event.kind is EvaluationEventKind.CACHE_HIT
        ]
        hit_operations = {event.operation_id for event in hits}
        self.assertTrue(
            {
                "zencad.typed.edge.curve",
                "zencad.typed.face.surface",
                "zencad.typed.shape.boundbox",
                "zencad.typed.shape.to-mesh",
            }
            <= hit_operations
        )


if __name__ == "__main__":
    unittest.main()
