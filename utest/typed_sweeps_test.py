import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore

from zencad import _typed as typed


class TypedBasicSweepsTest(unittest.TestCase):
    def test_extrude_and_revol_are_policy_independent(self):
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
                    profile = runtime.rectangle(1, 2, center=True)
                    extruded = runtime.extrude(
                        profile,
                        runtime.vector3(0, 0, 4),
                        center=True,
                    )
                    linear = profile.linear_extrude(4, center=True)
                    revolved = runtime.revol(profile, 3)
                    partial = profile.revol(3, math.pi)
                    first_section = runtime.rectangle_wire(1, 2, center=True)
                    second_section = runtime.rectangle_wire(2, 1, center=True).up(3)
                    lofted = runtime.loft((first_section, second_section))
                    loft_shell = runtime.loft(
                        (first_section, second_section),
                        smooth=True,
                        shell=True,
                    )

                    observed_types.add(
                        (
                            type(extruded),
                            type(linear),
                            type(revolved),
                            type(partial),
                            type(lofted),
                            type(loft_shell),
                        )
                    )
                    self.assertIs(type(extruded), typed.Shape)
                    self.assertIs(type(linear), typed.Shape)
                    self.assertIs(type(revolved), typed.Shape)
                    self.assertIs(type(partial), typed.Shape)
                    self.assertIs(type(lofted), typed.Solid)
                    self.assertIs(type(loft_shell), typed.Shell)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertAlmostEqual(extruded.mass().value(), 8)
                    self.assertAlmostEqual(linear.mass().value(), 8)
                    self.assertAlmostEqual(revolved.mass().value(), 12 * math.pi)
                    self.assertAlmostEqual(partial.mass().value(), 6 * math.pi)
                    self.assertGreater(lofted.mass().value(), 0)
                    self.assertGreater(loft_shell.mass().value(), 0)
                    bounds = extruded.boundbox().value()
                    self.assertAlmostEqual(bounds.zmin, -2.0000001)
                    self.assertAlmostEqual(bounds.zmax, 2.0000001)

        self.assertEqual(len(observed_types), 1)

    def test_scalar_inputs_remain_in_the_graph(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        seed = runtime.box(2)
        profile = runtime.rectangle(seed.mass() / 8, seed.mass() / 4, center=True)
        extruded = runtime.linear_extrude(profile, seed.mass() / 2, center=True)
        revolved = runtime.revol(profile, seed.mass() * 3 / 8, math.pi)

        self.assertEqual(events, [])
        self.assertAlmostEqual(extruded.mass().value(), 8)
        self.assertAlmostEqual(revolved.mass().value(), 6 * math.pi)
        self.assertTrue(events)

    def test_invalid_inputs_fail_at_the_typed_or_resolved_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        profile = runtime.rectangle(1, 2)

        with self.assertRaisesRegex(TypeError, "extrude expects Shape"):
            runtime.extrude(runtime.point3(), 2)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "extrude center must be bool"):
            runtime.extrude(profile, 2, center=1)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.extrude(other.rectangle(1, 2), 2)
        with self.assertRaisesRegex(ValueError, "at least two sections"):
            runtime.loft((runtime.rectangle_wire(1, 2),))
        with self.assertRaisesRegex(TypeError, "only Edge or Wire"):
            runtime.loft((profile, runtime.rectangle_wire(1, 2)))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "loft smooth must be bool"):
            runtime.loft(
                (runtime.rectangle_wire(1, 2), runtime.rectangle_wire(2, 1).up(2)),
                smooth=1,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "max_degree must be positive"):
            runtime.loft(
                (runtime.rectangle_wire(1, 2), runtime.rectangle_wire(2, 1).up(2)),
                max_degree=0,
            )
        with self.assertRaisesRegex(ValueError, "revol radius must be finite"):
            runtime.revol(profile, math.inf).native()
        with self.assertRaisesRegex(ValueError, "revol yaw must be finite"):
            runtime.revol(profile, 3, math.nan).native()

        immediate = typed.Runtime.immediate(cache=False)
        with self.assertRaisesRegex(ValueError, "revol radius must be finite"):
            immediate.revol(immediate.rectangle(1, 2), math.inf)

    def test_revol_restores_from_shared_cache(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.revol(first.rectangle(1, 2, center=True), 3).native()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.revol(second.rectangle(1, 2, center=True), 3)
        self.assertAlmostEqual(restored.mass().value(), 12 * math.pi)
        self.assertTrue(
            any(
                event.kind is EvaluationEventKind.CACHE_HIT
                and event.operation_id == "zencad.typed.shape.revol"
                for event in events
            )
        )


if __name__ == "__main__":
    unittest.main()
