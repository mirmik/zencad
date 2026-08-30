import json
import math
import os
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
from OCP.Geom import Geom_Circle, Geom_Curve
from OCP.Geom2d import Geom2d_Curve, Geom2d_Ellipse
from OCP.gp import gp_Ax2, gp_Ax2d, gp_Dir, gp_Dir2d, gp_Pnt, gp_Pnt2d

from zencad import _typed as typed
from zencad._typed import _curve_operations as curve_ops
from zencad._typed._serialization import Curve2Serializer


class TypedCurveHandlesTest(unittest.TestCase):
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
                    line = runtime.line(
                        runtime.point(1, 2, 3),
                        runtime.vector(1, 0, 0),
                    )
                    circle = runtime.circle(2)
                    ellipse = runtime.ellipse(3, 2)
                    segment = runtime.segment2(
                        runtime.point2(0, 0),
                        runtime.point2(4, 0),
                    )
                    ellipse2 = runtime.ellipse2(3, 2)
                    trimmed = segment.trim(0.5, 2.5)

                    policy_types = tuple(
                        type(value)
                        for value in (
                            line,
                            circle,
                            ellipse,
                            segment,
                            ellipse2,
                            trimmed,
                        )
                    )
                    observed_types.add(policy_types)
                    self.assertEqual(
                        policy_types,
                        (
                            typed.Curve,
                            typed.Curve,
                            typed.Curve,
                            typed.Curve2,
                            typed.Curve2,
                            typed.Curve2,
                        ),
                    )
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertEqual(line.point(3).value(), (4.0, 2.0, 3.0))
                    self.assertEqual(line.tangent(3).value(), (1.0, 0.0, 0.0))
                    self.assertEqual(circle.point(0).value(), (2.0, 0.0, 0.0))
                    self.assertEqual(circle.tangent(0).value(), (-0.0, 2.0, 0.0))
                    self.assertEqual(ellipse.point(0).value(), (3.0, 0.0, 0.0))
                    self.assertEqual(segment.point(2).value(), (2.0, 0.0))
                    self.assertEqual(segment.tangent(2).value(), (1.0, 0.0))
                    self.assertEqual(ellipse2.point(0).value(), (3.0, 0.0))
                    self.assertEqual(trimmed.point(0.5).value(), (0.5, 0.0))
                    self.assertEqual(trimmed.point(2.5).value(), (2.5, 0.0))
                    self.assertEqual(
                        tuple(float(value) for value in circle.range()),
                        (0.0, 2 * math.pi),
                    )
                    self.assertEqual(
                        tuple(float(value) for value in trimmed.range()),
                        (0.5, 2.5),
                    )
                    self.assertIs(type(circle.native()), Geom_Circle)
                    self.assertIsInstance(segment.native(), Geom2d_Curve)
                    self.assertIs(circle.unlazy(), circle)
                    self.assertIs(trimmed.unlazy(), trimmed)

        self.assertEqual(len(observed_types), 1)

    def test_scalar_point_and_vector_inputs_remain_in_the_graph(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = runtime.box(2)
        radius = seed.mass() / 4
        origin = seed.center()

        circle = runtime.circle(radius)
        ellipse = runtime.ellipse(radius + 1, radius)
        line = runtime.line(origin, runtime.vector(radius, 0, 0))
        segment = runtime.segment2(
            runtime.point2(0, 0),
            runtime.point2(radius * 2, 0),
        )
        ellipse2 = runtime.ellipse2(radius + 1, radius)
        trimmed = runtime.trim_curve2(segment, radius / 4, radius + 0.5)

        self.assertEqual(events, [])
        self.assertEqual(circle.point(0).value(), (2.0, 0.0, 0.0))
        self.assertEqual(ellipse.point(0).value(), (3.0, 0.0, 0.0))
        self.assertEqual(line.point(3).value(), (4.0, 1.0, 1.0))
        self.assertEqual(segment.point(4).value(), (4.0, 0.0))
        self.assertEqual(ellipse2.point(0).value(), (3.0, 0.0))
        self.assertEqual(
            tuple(float(value) for value in trimmed.range()),
            (0.5, 2.5),
        )
        self.assertTrue(events)

    def test_native_boundaries_are_owned_snapshots(self):
        runtime = typed.Runtime.deferred(cache=False)

        source = Geom_Circle(
            gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
            2,
        )
        curve = typed.Curve.from_ocp(source, runtime=runtime)
        self.assertIs(get_type_hints(typed.Curve.native)["return"], Geom_Curve)
        source.SetRadius(9)
        first = curve.native()
        first.SetRadius(7)
        self.assertEqual(curve.native().Radius(), 2.0)

        source2 = Geom2d_Ellipse(
            gp_Ax2d(gp_Pnt2d(0, 0), gp_Dir2d(1, 0)),
            3,
            2,
        )
        curve2 = typed.Curve2.from_ocp(source2, runtime=runtime)
        self.assertIs(get_type_hints(typed.Curve2.native)["return"], Geom2d_Curve)
        source2.SetMajorRadius(8)
        first2 = curve2.native()
        first2.SetMajorRadius(7)
        self.assertEqual(curve2.native().MajorRadius(), 3.0)

        with self.assertRaisesRegex(TypeError, "Geom_Curve"):
            typed.Curve.from_ocp(source2, runtime=runtime)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "Geom2d_Curve"):
            typed.Curve2.from_ocp(source, runtime=runtime)  # type: ignore[arg-type]

    def test_invalid_inputs_fail_at_the_typed_or_resolved_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "origin must be Point3"):
            runtime.line(runtime.point2(0, 0), runtime.vector(1, 0, 0))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.line(runtime.point(0, 0, 0), other.vector(1, 0, 0))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.segment2(runtime.point2(0, 0), other.point2(1, 0))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.trim_curve2(other.ellipse2(2, 1), 0, 1)

        invalid = runtime.circle(0)
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            invalid.native()
        with self.assertRaisesRegex(ValueError, "non-zero Vector3"):
            runtime.line(runtime.point(0, 0, 0), runtime.vector(0, 0, 0)).native()
        with self.assertRaisesRegex(ValueError, "must not be less"):
            runtime.ellipse(1, 2).native()
        with self.assertRaisesRegex(ValueError, "endpoints must be distinct"):
            point = runtime.point2(0, 0)
            runtime.segment2(point, point).native()

        immediate = typed.Runtime.immediate(cache=False)
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            immediate.circle(0)


class TypedCurveCacheTest(unittest.TestCase):
    def test_curve_cache_uses_family_specific_non_pickle_artifacts(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.circle(2).native()

        self.assertEqual(len(store.records), 1)
        key, record = next(iter(store.records.items()))
        self.assertEqual(record.result_type_id, "zencad.typed.Curve.v1")
        self.assertEqual(
            record.serializer_id,
            "zencad.curve.occt-compact-artifact.v1",
        )
        self.assertEqual(record.value.payload, b"zencad.typed.curve\x00v1")
        self.assertEqual(record.value.artifacts[0].name, "curve.geom")
        self.assertGreater(len(record.value.artifacts[0].data), 10)

        wrong_native = typed.Runtime.deferred(cache=False).ellipse2(3, 2).native()
        wrong_value = Curve2Serializer().dumps(curve_ops.curve2_from_ocp(wrong_native))
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
        restored = second.circle(2)
        self.assertIs(type(restored.native()), Geom_Circle)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_runtime_and_fresh_process_reuse_curve_cache(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.ellipse2(3, 2).native()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        self.assertIsInstance(second.ellipse2(3, 2).native(), Geom2d_Ellipse)
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
runtime.circle(2).point(0).value()
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
