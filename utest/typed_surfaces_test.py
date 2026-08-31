import json
import math
import os
from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import get_type_hints
import unittest

from evalcache.v2 import (
    CacheRecord,
    EvaluationEventKind,
    EvaluationMode,
    MemoryCacheStore,
)
from OCP.Geom import (
    Geom_BSplineSurface,
    Geom_Circle,
    Geom_CylindricalSurface,
    Geom_Surface,
    Geom_TrimmedCurve,
)
from OCP.Geom2d import Geom2d_Ellipse
from OCP.gp import (
    gp_Ax2,
    gp_Ax2d,
    gp_Ax3,
    gp_Dir,
    gp_Dir2d,
    gp_Pnt,
    gp_Pnt2d,
)

from zencad import _typed as typed
from zencad._typed import _curve_operations as curve_ops
from zencad._typed._serialization import CurveSerializer


def _assert_coordinates(
    testcase: unittest.TestCase,
    actual: tuple[float, ...],
    expected: tuple[float, ...],
) -> None:
    testcase.assertEqual(len(actual), len(expected))
    for left, right in zip(actual, expected):
        testcase.assertAlmostEqual(left, right, places=10)


class TypedSurfaceHandlesTest(unittest.TestCase):
    def test_factories_and_queries_are_policy_independent(self):
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
                    cylinder = runtime.cylinder_surface(2)
                    section = runtime.circle_curve(1)
                    spine = runtime.circle_curve(3)
                    sweep = runtime.sweep_surface(section, spine)
                    scale_law = runtime.constant_sweep_scale(1, spine.range())
                    section_law = runtime.evolved_sweep_section(section, scale_law)
                    location_law = runtime.sweep_location(spine)
                    law_sweep = runtime.sweep_surface_from_laws(
                        section_law,
                        location_law,
                    )
                    mapped = cylinder.map(
                        runtime.segment2(
                            runtime.point2(0, 0),
                            runtime.point2(math.pi / 2, 3),
                        )
                    )

                    observed_types.add((type(cylinder), type(sweep), type(mapped)))
                    self.assertIs(type(cylinder), typed.Surface)
                    self.assertIs(type(sweep), typed.Surface)
                    self.assertIs(type(scale_law), typed.SweepScaleLaw)
                    self.assertIs(type(section_law), typed.SweepSectionLaw)
                    self.assertIs(type(location_law), typed.SweepLocationLaw)
                    self.assertIs(type(law_sweep), typed.Surface)
                    self.assertIs(type(mapped), typed.Edge)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    _assert_coordinates(
                        self,
                        cylinder.point(0, 3).value(),
                        (2.0, 0.0, 3.0),
                    )
                    _assert_coordinates(
                        self,
                        cylinder.normal(0, 3).value(),
                        (1.0, 0.0, 0.0),
                    )
                    self.assertEqual(
                        tuple(float(value) for value in cylinder.u_range()),
                        (0.0, 2 * math.pi),
                    )
                    self.assertEqual(
                        tuple(float(value) for value in cylinder.v_range()),
                        (-2e100, 2e100),
                    )
                    self.assertIs(type(cylinder.u_iso(0)), typed.Curve)
                    self.assertIs(type(cylinder.v_iso(3)), typed.Curve)
                    _assert_coordinates(
                        self,
                        cylinder.u_iso(0).point(3).value(),
                        (2.0, 0.0, 3.0),
                    )
                    _assert_coordinates(
                        self,
                        cylinder.v_iso(3).point(0).value(),
                        (2.0, 0.0, 3.0),
                    )
                    self.assertIs(type(cylinder.native()), Geom_CylindricalSurface)
                    self.assertIs(type(sweep.native()), Geom_BSplineSurface)
                    self.assertIs(type(law_sweep.native()), Geom_BSplineSurface)
                    mapped_endpoints = mapped.endpoints()
                    _assert_coordinates(self, mapped_endpoints[0].value(), (2, 0, 0))
                    _assert_coordinates(self, mapped_endpoints[1].value(), (0, 2, 3))
                    self.assertEqual(
                        tuple(float(value) for value in sweep.u_range()),
                        (0.0, 2 * math.pi),
                    )
                    self.assertEqual(
                        tuple(float(value) for value in sweep.v_range()),
                        (0.0, 2 * math.pi),
                    )
                    self.assertIs(cylinder.unlazy(), cylinder)
                    self.assertIs(sweep.unlazy(), sweep)

        self.assertEqual(len(observed_types), 1)

    def test_sweep_laws_are_immutable_graph_compositions(self):
        runtime = typed.Runtime.deferred(cache=False)
        section = runtime.circle_curve(1)
        spine = runtime.circle_curve(3)
        scale = runtime.constant_sweep_scale(2, spine.range())
        section_law = runtime.evolved_sweep_section(section, scale)
        location = runtime.sweep_location(spine, typed.SweepTrihedron.FRENET)

        self.assertIs(scale.runtime, runtime)
        self.assertIs(section_law.runtime, runtime)
        self.assertIs(location.runtime, runtime)
        self.assertEqual(scale.scale.value(), 2)
        self.assertEqual(scale.domain.value(), (0, 2 * math.pi))
        self.assertIs(section_law.section, section)
        self.assertIs(section_law.scale, scale)
        self.assertIs(location.spine, spine)
        self.assertIs(location.trihedron, typed.SweepTrihedron.FRENET)
        self.assertIs(scale.unlazy(), scale)
        self.assertIs(section_law.unlazy(), section_law)
        self.assertIs(location.unlazy(), location)

        with self.assertRaises(FrozenInstanceError):
            scale.scale = runtime.scalar(3)  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            location.trihedron = typed.SweepTrihedron.CORRECTED_FRENET  # type: ignore[misc]

    def test_scalar_and_curve_inputs_remain_in_the_graph(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = runtime.box(2)
        radius = seed.mass() / 4
        scale = seed.mass() / 8
        cylinder = runtime.cylinder_surface(radius)
        sweep = runtime.sweep_surface(
            runtime.circle_curve(radius / 2),
            runtime.circle_curve(radius + 1),
            scale=scale,
            trihedron=typed.SweepTrihedron.FRENET,
        )
        point = cylinder.point(seed.center().x, seed.center().z)
        normal = cylinder.normal(seed.center().x, seed.center().z)
        iso = cylinder.v_iso(seed.center().z)
        mapped = cylinder.map(
            runtime.segment2(
                runtime.point2(0, 0),
                runtime.point2(seed.center().x, seed.center().z),
            )
        )

        self.assertEqual(events, [])
        _assert_coordinates(
            self,
            point.value(),
            (2 * math.cos(1), 2 * math.sin(1), 1),
        )
        _assert_coordinates(
            self,
            normal.value(),
            (math.cos(1), math.sin(1), 0),
        )
        _assert_coordinates(
            self,
            iso.point(0).value(),
            (2.0, 0.0, 1.0),
        )
        _assert_coordinates(
            self,
            mapped.endpoints()[1].value(),
            (2 * math.cos(1), 2 * math.sin(1), 1),
        )
        self.assertIs(type(sweep.native()), Geom_BSplineSurface)
        self.assertTrue(events)

    def test_native_boundaries_preserve_full_precision_and_ownership(self):
        runtime = typed.Runtime.deferred(cache=False)
        coordinate = 0.123456789012345
        radius = 2.123456789012345
        source = Geom_CylindricalSurface(
            gp_Ax3(gp_Pnt(coordinate, 0, 0), gp_Dir(0, 0, 1)),
            radius,
        )
        surface = typed.Surface.from_ocp(source, runtime=runtime)
        self.assertIs(get_type_hints(typed.Surface.native)["return"], Geom_Surface)
        source.SetRadius(9)
        first = surface.native()
        first.SetRadius(7)
        restored = surface.native()
        self.assertEqual(restored.Location().X(), coordinate)
        self.assertEqual(restored.Radius(), radius)

        curve = typed.Curve.from_ocp(
            Geom_Circle(
                gp_Ax2(gp_Pnt(coordinate, 0, 0), gp_Dir(0, 0, 1)),
                radius,
            ),
            runtime=runtime,
        ).native()
        self.assertEqual(curve.Location().X(), coordinate)
        self.assertEqual(curve.Radius(), radius)

        curve2 = typed.Curve2.from_ocp(
            Geom2d_Ellipse(
                gp_Ax2d(gp_Pnt2d(coordinate, 0), gp_Dir2d(1, 0)),
                radius,
                1.1,
            ),
            runtime=runtime,
        ).native()
        self.assertEqual(curve2.Location().X(), coordinate)
        self.assertEqual(curve2.MajorRadius(), radius)

        with self.assertRaisesRegex(TypeError, "Geom_Surface"):
            typed.Surface.from_ocp(curve, runtime=runtime)  # type: ignore[arg-type]

    def test_sweep_scale_law_uses_the_spine_parameter_domain(self):
        runtime = typed.Runtime.deferred(cache=False)
        spine = typed.Curve.from_ocp(
            Geom_TrimmedCurve(
                Geom_Circle(
                    gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
                    3,
                ),
                0,
                math.pi,
            ),
            runtime=runtime,
        )

        surface = runtime.sweep_surface(runtime.circle_curve(1), spine)

        _assert_coordinates(
            self,
            tuple(float(value) for value in surface.v_range()),
            (0.0, math.pi),
        )

    def test_invalid_inputs_fail_at_the_typed_or_resolved_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "section must be Curve"):
            runtime.sweep_surface(runtime.ellipse2(2, 1), runtime.circle_curve(3))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.sweep_surface(runtime.circle_curve(1), other.circle_curve(3))
        with self.assertRaisesRegex(TypeError, "domain must be Interval"):
            runtime.constant_sweep_scale(1, (0, 1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.constant_sweep_scale(1, other.circle_curve(3).range())
        with self.assertRaisesRegex(TypeError, "scale must be SweepScaleLaw"):
            runtime.evolved_sweep_section(
                runtime.circle_curve(1),
                1,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "trihedron must be SweepTrihedron"):
            runtime.sweep_location(
                runtime.circle_curve(3),
                "frenet",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.sweep_surface_from_laws(
                runtime.evolved_sweep_section(
                    runtime.circle_curve(1),
                    runtime.constant_sweep_scale(
                        1,
                        runtime.circle_curve(3).range(),
                    ),
                ),
                other.sweep_location(other.circle_curve(3)),
            )
        with self.assertRaisesRegex(TypeError, "expects Curve2"):
            runtime.cylinder_surface(2).map(runtime.circle_curve(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.cylinder_surface(2).map(
                other.segment2(other.point2(0, 0), other.point2(1, 1))
            )
        with self.assertRaisesRegex(TypeError, "must be SweepTrihedron"):
            runtime.sweep_surface(
                runtime.circle_curve(1),
                runtime.circle_curve(3),
                trihedron="frenet",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "tolerance must be int or float"):
            runtime.sweep_surface(
                runtime.circle_curve(1),
                runtime.circle_curve(3),
                tolerance=True,
            )
        with self.assertRaisesRegex(ValueError, "between 0 and 3"):
            runtime.sweep_surface(
                runtime.circle_curve(1),
                runtime.circle_curve(3),
                continuity=4,
            )
        with self.assertRaisesRegex(ValueError, "max_degree must be positive"):
            runtime.sweep_surface(
                runtime.circle_curve(1),
                runtime.circle_curve(3),
                max_degree=0,
            )

        with self.assertRaisesRegex(ValueError, "positive scalar"):
            runtime.cylinder_surface(0).native()
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            runtime.sweep_surface(
                runtime.circle_curve(1),
                runtime.circle_curve(3),
                scale=0,
            ).native()
        with self.assertRaisesRegex(ValueError, "domain must be increasing"):
            runtime.sweep_surface_from_laws(
                runtime.evolved_sweep_section(
                    runtime.circle_curve(1),
                    runtime.constant_sweep_scale(
                        1,
                        typed.Interval(runtime.scalar(1), runtime.scalar(0)),
                    ),
                ),
                runtime.sweep_location(runtime.circle_curve(3)),
            ).native()

        immediate = typed.Runtime.immediate(cache=False)
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            immediate.cylinder_surface(0)


class TypedSurfaceCacheTest(unittest.TestCase):
    def test_mapped_edge_restores_from_shared_cache(self):
        store = MemoryCacheStore()

        def mapped(runtime: typed.Runtime) -> typed.Edge:
            return runtime.cylinder_surface(2).map(
                runtime.segment2(
                    runtime.point2(0, 0),
                    runtime.point2(math.pi / 2, 3),
                )
            )

        first = typed.Runtime.deferred(cache=True, cache_store=store)
        self.assertFalse(mapped(first).native().IsNull())

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        self.assertFalse(mapped(second).native().IsNull())
        self.assertTrue(
            any(
                event.kind is EvaluationEventKind.CACHE_HIT
                and event.operation_id == "zencad.typed.surface.map"
                for event in events
            )
        )

    def test_surface_cache_uses_non_pickle_artifact_and_rejects_curve(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.cylinder_surface(2).native()

        self.assertEqual(len(store.records), 1)
        key, record = next(iter(store.records.items()))
        self.assertEqual(record.result_type_id, "zencad.typed.Surface.v1")
        self.assertEqual(
            record.serializer_id,
            "zencad.surface.occt-set-artifact.v1",
        )
        self.assertEqual(record.value.payload, b"zencad.typed.surface\x00v1")
        self.assertEqual(record.value.artifacts[0].name, "surface.geom")
        self.assertGreater(len(record.value.artifacts[0].data), 20)

        wrong_native = typed.Runtime.deferred(cache=False).circle_curve(2).native()
        wrong_value = CurveSerializer().dumps(curve_ops.curve_from_ocp(wrong_native))
        store.records[key] = CacheRecord(
            schema=record.schema,
            result_type_id=record.result_type_id,
            serializer_id=record.serializer_id,
            value=wrong_value,
        )

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.cylinder_surface(2)
        self.assertIs(type(restored.native()), Geom_CylindricalSurface)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_runtime_and_fresh_process_reuse_surface_cache(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.sweep_surface(first.circle_curve(1), first.circle_curve(3)).native()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.sweep_surface(
            second.circle_curve(1), second.circle_curve(3)
        ).native()
        self.assertIs(type(restored), Geom_BSplineSurface)
        self.assertIn(
            EvaluationEventKind.CACHE_HIT,
            [event.kind for event in events],
        )

        script = """
import json
import sys
from collections import Counter

from evalcache import DirCache_v2
from evalcache.v2 import MappingCacheStore
from zencad import _typed as typed

events = []
runtime = typed.Runtime.deferred(
    cache=True,
    cache_store=MappingCacheStore(DirCache_v2(sys.argv[1])),
    progress_hooks=(events.append,),
)
runtime.cylinder_surface(2).point(0, 3).value()
print(json.dumps(Counter(event.kind.value for event in events)))
"""
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            roots = [
                str(Path(__file__).resolve().parents[1]),
                "/home/mirmik/project/evalcache",
            ]
            environment["PYTHONPATH"] = os.pathsep.join(
                roots + [environment.get("PYTHONPATH", "")]
            )
            first_process = subprocess.run(
                [sys.executable, "-c", script, directory],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            second_process = subprocess.run(
                [sys.executable, "-c", script, directory],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

        first_counts = json.loads(first_process.stdout.strip().splitlines()[-1])
        second_counts = json.loads(second_process.stdout.strip().splitlines()[-1])
        self.assertGreater(first_counts.get("cache_store", 0), 0)
        self.assertGreater(second_counts.get("cache_hit", 0), 0)
        self.assertEqual(second_counts.get("cache_store", 0), 0)


if __name__ == "__main__":
    unittest.main()
