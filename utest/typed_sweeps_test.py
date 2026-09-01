import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_context


class TypedBasicSweepsTest(unittest.TestCase):
    def test_sweep_family_is_declared_at_module_level(self):
        for name in ("extrude", "revol", "loft", "pipe", "pipe_shell", "revol2"):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        context = typed.Context.deferred(cache=False)
        profile = context.call(typed.rectangle, 1, 2)
        first = context.call(typed.rectangle_wire, 1, 2)
        second = context.call(typed.rectangle_wire, 2, 1).up(3)
        pipe_profile = context.call(typed.circle, 1, wire=True)
        spine = context.call(
            typed.segment,
            context.call(
                typed.point3,
            ),
            context.call(typed.point3, 0, 0, 5),
        )
        with using_context(context):
            values = (
                typed.extrude(profile, 3),
                typed.linear_extrude(profile, 3),
                typed.revol(profile, 3),
                typed.loft((first, second)),
                typed.pipe(pipe_profile, spine),
                typed.pipe_shell((pipe_profile,), spine),
                typed.sweep(pipe_profile, spine),
                typed.revol2(profile, 3, sections=8),
            )

        self.assertTrue(all(value.context is context for value in values))
        self.assertEqual(
            tuple(value._state.operation_id for value in values),
            (
                "zencad.typed.shape.extrude",
                "zencad.typed.shape.extrude",
                "zencad.typed.shape.revol",
                "zencad.typed.loft",
                "zencad.typed.pipe",
                "zencad.typed.pipe_shell",
                "zencad.typed.pipe_shell",
                "zencad.typed.revol2",
            ),
        )

    def test_extrude_and_revol_are_policy_independent(self):
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
                    profile = context.call(typed.rectangle, 1, 2, center=True)
                    extruded = context.call(
                        typed.extrude,
                        profile,
                        context.call(typed.vector3, 0, 0, 4),
                        center=True,
                    )
                    linear = profile.linear_extrude(4, center=True)
                    revolved = context.call(typed.revol, profile, 3)
                    partial = profile.revol(3, math.pi)
                    first_section = context.call(
                        typed.rectangle_wire, 1, 2, center=True
                    )
                    second_section = context.call(
                        typed.rectangle_wire, 2, 1, center=True
                    ).up(3)
                    lofted = context.call(typed.loft, (first_section, second_section))
                    loft_shell = context.call(
                        typed.loft,
                        (first_section, second_section),
                        smooth=True,
                        shell=True,
                    )
                    pipe_profile = context.call(typed.circle, 1, wire=True)
                    pipe_spine = context.call(
                        typed.segment,
                        context.call(typed.point3, 0, 0, 0),
                        context.call(typed.point3, 0, 0, 5),
                    )
                    piped = context.call(
                        typed.pipe,
                        pipe_profile,
                        pipe_spine,
                        trihedron=typed.PipeTrihedron.DISCRETE,
                    )
                    pipe_solid = context.call(
                        typed.pipe_shell,
                        (pipe_profile,),
                        pipe_spine,
                        transition=typed.PipeTransition.ROUND_CORNER,
                    )
                    pipe_surface = context.call(
                        typed.pipe_shell,
                        (pipe_profile,),
                        pipe_spine,
                        binormal=context.call(typed.vector3, 1, 0, 0),
                        solid=False,
                    )
                    swept = context.call(
                        typed.sweep, pipe_profile, pipe_spine, frenet=True
                    )
                    rolled = context.call(
                        typed.revol2,
                        profile,
                        3,
                        sections=8,
                        yaw=(0, math.pi),
                        roll=(0, math.pi / 2),
                    )
                    full_rolled = context.call(
                        typed.revol2,
                        profile,
                        3,
                        sections=8,
                    )

                    observed_types.add(
                        (
                            type(extruded),
                            type(linear),
                            type(revolved),
                            type(partial),
                            type(lofted),
                            type(loft_shell),
                            type(piped),
                            type(pipe_solid),
                            type(pipe_surface),
                            type(swept),
                            type(rolled),
                        )
                    )
                    self.assertIs(type(extruded), typed.Shape)
                    self.assertIs(type(linear), typed.Shape)
                    self.assertIs(type(revolved), typed.Shape)
                    self.assertIs(type(partial), typed.Shape)
                    self.assertIs(type(lofted), typed.Solid)
                    self.assertIs(type(loft_shell), typed.Shell)
                    self.assertIs(type(piped), typed.Shape)
                    self.assertIs(type(pipe_solid), typed.Solid)
                    self.assertIs(type(pipe_surface), typed.Shell)
                    self.assertIs(type(swept), typed.Solid)
                    self.assertIs(type(rolled), typed.Solid)
                    self.assertIs(type(full_rolled), typed.Solid)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertAlmostEqual(extruded.mass().value(), 8)
                    self.assertAlmostEqual(linear.mass().value(), 8)
                    self.assertGreater(full_rolled.mass().value(), 0)
                    self.assertAlmostEqual(revolved.mass().value(), 12 * math.pi)
                    self.assertAlmostEqual(partial.mass().value(), 6 * math.pi)
                    self.assertGreater(lofted.mass().value(), 0)
                    self.assertGreater(loft_shell.mass().value(), 0)
                    self.assertGreater(piped.mass().value(), 0)
                    self.assertAlmostEqual(pipe_solid.mass().value(), 5 * math.pi)
                    self.assertGreater(pipe_surface.mass().value(), 0)
                    self.assertAlmostEqual(swept.mass().value(), 5 * math.pi)
                    self.assertGreater(rolled.mass().value(), 0)
                    bounds = extruded.boundbox().value()
                    self.assertAlmostEqual(bounds.zmin, -2.0000001)
                    self.assertAlmostEqual(bounds.zmax, 2.0000001)

        self.assertEqual(len(observed_types), 1)

    def test_scalar_inputs_remain_in_the_graph(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        seed = context.call(typed.box, 2)
        profile = context.call(
            typed.rectangle, seed.mass() / 8, seed.mass() / 4, center=True
        )
        extruded = context.call(
            typed.linear_extrude, profile, seed.mass() / 2, center=True
        )
        revolved = context.call(typed.revol, profile, seed.mass() * 3 / 8, math.pi)

        self.assertEqual(events, [])
        self.assertAlmostEqual(extruded.mass().value(), 8)
        self.assertAlmostEqual(revolved.mass().value(), 6 * math.pi)
        self.assertTrue(events)

    def test_pipe_modes_and_transitions_are_explicit(self):
        context = typed.Context.deferred(cache=False)
        profile = context.call(typed.circle, 1, wire=True)
        spine = context.call(
            typed.segment,
            context.call(
                typed.point3,
            ),
            context.call(typed.point3, 0, 0, 5),
        )

        self.assertEqual(len(tuple(typed.PipeTrihedron)), 10)
        for trihedron in typed.PipeTrihedron:
            with self.subTest(trihedron=trihedron):
                self.assertGreater(
                    context.call(typed.pipe, profile, spine, trihedron=trihedron)
                    .mass()
                    .value(),
                    0,
                )
        for transition in typed.PipeTransition:
            with self.subTest(transition=transition):
                self.assertAlmostEqual(
                    context.call(
                        typed.pipe_shell,
                        (profile,),
                        spine,
                        transition=transition,
                    )
                    .mass()
                    .value(),
                    5 * math.pi,
                )

    def test_invalid_inputs_fail_at_the_typed_or_resolved_boundary(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)
        profile = context.call(typed.rectangle, 1, 2)

        with self.assertRaises(TypeError):
            context.call(typed.extrude, context.call(typed.point3), 2).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "extrude center must be bool"):
            context.call(typed.extrude, profile, 2, center=1).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.extrude, other.call(typed.rectangle, 1, 2), 2)
        with self.assertRaisesRegex(ValueError, "at least two sections"):
            context.call(
                typed.loft, (context.call(typed.rectangle_wire, 1, 2),)
            ).native()
        with self.assertRaises(TypeError):
            context.call(
                typed.loft, (profile, context.call(typed.rectangle_wire, 1, 2))
            ).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "loft smooth must be bool"):
            context.call(
                typed.loft,
                (
                    context.call(typed.rectangle_wire, 1, 2),
                    context.call(typed.rectangle_wire, 2, 1).up(2),
                ),
                smooth=1,  # type: ignore[arg-type]
            ).native()
        with self.assertRaisesRegex(ValueError, "max_degree must be positive"):
            context.call(
                typed.loft,
                (
                    context.call(typed.rectangle_wire, 1, 2),
                    context.call(typed.rectangle_wire, 2, 1).up(2),
                ),
                max_degree=0,
            ).native()
        pipe_profile = context.call(typed.circle, 1, wire=True)
        pipe_spine = context.call(
            typed.segment,
            context.call(
                typed.point3,
            ),
            context.call(typed.point3, 0, 0, 5),
        )
        with self.assertRaisesRegex(TypeError, "trihedron must be PipeTrihedron"):
            context.call(
                typed.pipe,
                pipe_profile,
                pipe_spine,
                trihedron="frenet",  # type: ignore[arg-type]
            ).native()
        with self.assertRaises(TypeError):
            context.call(typed.pipe, pipe_profile, profile).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.pipe,
                pipe_profile,
                other.call(
                    typed.segment,
                    other.call(
                        typed.point3,
                    ),
                    other.call(typed.point3, 0, 0, 5),
                ),
            )
        with self.assertRaisesRegex(TypeError, "transition must be PipeTransition"):
            context.call(
                typed.pipe_shell,
                (pipe_profile,),
                pipe_spine,
                transition=0,  # type: ignore[arg-type]
            ).native()
        with self.assertRaisesRegex(
            ValueError, "orientation modes are mutually exclusive"
        ):
            context.call(
                typed.pipe_shell,
                (pipe_profile,),
                pipe_spine,
                frenet=True,
                discrete=True,
            ).native()
        with self.assertRaisesRegex(ValueError, "sections must be at least two"):
            context.call(typed.revol2, profile, 3, sections=1).native()
        with self.assertRaisesRegex(ValueError, "at least two per part"):
            context.call(typed.revol2, profile, 3, sections=4, parts=3).native()
        with self.assertRaisesRegex(ValueError, "radius must be finite and positive"):
            context.call(typed.revol2, profile, 0).native()
        with self.assertRaisesRegex(ValueError, "yaw interval must be non-empty"):
            context.call(typed.revol2, profile, 3, yaw=(1, 1)).native()
        with self.assertRaisesRegex(ValueError, "revol radius must be finite"):
            context.call(typed.revol, profile, math.inf).native()
        with self.assertRaisesRegex(ValueError, "revol yaw must be finite"):
            context.call(typed.revol, profile, 3, math.nan).native()

        immediate = typed.Context.immediate(cache=False)
        with self.assertRaisesRegex(ValueError, "revol radius must be finite"):
            immediate.call(typed.revol, immediate.call(typed.rectangle, 1, 2), math.inf)

    def test_revol_restores_from_shared_cache(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(
            typed.revol, first.call(typed.rectangle, 1, 2, center=True), 3
        ).native()

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.call(
            typed.revol, second.call(typed.rectangle, 1, 2, center=True), 3
        )
        self.assertAlmostEqual(restored.mass().value(), 12 * math.pi)
        self.assertTrue(
            any(
                event.kind is EvaluationEventKind.CACHE_HIT
                and event.operation_id == "zencad.typed.shape.revol"
                for event in events
            )
        )

    def test_revol2_reuses_a_fresh_process_cache(self):
        script = """
import json
import math
import sys

from evalcache import DirCache_v2
from evalcache.v2 import EvaluationEventKind, MappingCacheStore
from zencad import _typed as typed

events = []
context = typed.Context.deferred(
    cache=True,
    cache_store=MappingCacheStore(DirCache_v2(sys.argv[1])),
    progress_hooks=(events.append,),
)
profile = context.call(typed.rectangle, 1, 2, center=True)
context.call(typed.revol2,
    profile,
    3,
    sections=8,
    yaw=(0, math.pi),
    roll=(0, math.pi / 2),
).native()
print(json.dumps({
    "stored": sum(event.kind is EvaluationEventKind.CACHE_STORE for event in events),
    "hits": [
        event.operation_id
        for event in events
        if event.kind is EvaluationEventKind.CACHE_HIT
    ],
}))
"""
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            roots = [
                str(Path(__file__).resolve().parents[1]),
                "/home/mirmik/project/termin-aurora/evalcache",
            ]
            environment["PYTHONPATH"] = os.pathsep.join(
                roots + [environment.get("PYTHONPATH", "")]
            )
            first = subprocess.run(
                [sys.executable, "-c", script, directory],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            second = subprocess.run(
                [sys.executable, "-c", script, directory],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

        first_result = json.loads(first.stdout.strip().splitlines()[-1])
        second_result = json.loads(second.stdout.strip().splitlines()[-1])
        self.assertGreater(first_result["stored"], 0)
        self.assertIn("zencad.typed.revol2", second_result["hits"])


if __name__ == "__main__":
    unittest.main()
