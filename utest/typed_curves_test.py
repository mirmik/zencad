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


def _assert_coordinates(
    testcase: unittest.TestCase,
    actual: tuple[float, ...],
    expected: tuple[float, ...],
) -> None:
    testcase.assertEqual(len(actual), len(expected))
    for left, right in zip(actual, expected):
        testcase.assertAlmostEqual(left, right, places=10)


class TypedCurveHandlesTest(unittest.TestCase):
    def test_factories_and_queries_are_policy_independent(self):
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
                    line = context.call(typed.line,
                        context.call(typed.point, 1, 2, 3),
                        context.call(typed.vector, 1, 0, 0),
                    )
                    circle = context.call(typed.circle_curve, 2)
                    ellipse = context.call(typed.ellipse_curve, 3, 2)
                    segment = context.call(typed.segment2,
                        context.call(typed.point2, 0, 0),
                        context.call(typed.point2, 4, 0),
                    )
                    ellipse2 = context.call(typed.ellipse2, 3, 2)
                    trimmed = segment.trim(0.5, 2.5)
                    rotated = segment.rotate(math.pi / 2)

                    policy_types = tuple(
                        type(value)
                        for value in (
                            line,
                            circle,
                            ellipse,
                            segment,
                            ellipse2,
                            trimmed,
                            rotated,
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
                    _assert_coordinates(self, rotated.point(2).value(), (0.0, 2.0))
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
        self.assertEqual(len(observed_types), 1)

    def test_scalar_point_and_vector_inputs_remain_in_the_graph(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = context.call(typed.box, 2)
        radius = seed.mass() / 4
        origin = seed.center()

        circle = context.call(typed.circle_curve, radius)
        ellipse = context.call(typed.ellipse_curve, radius + 1, radius)
        line = context.call(typed.line, origin, context.call(typed.vector, radius, 0, 0))
        segment = context.call(typed.segment2,
            context.call(typed.point2, 0, 0),
            context.call(typed.point2, radius * 2, 0),
        )
        ellipse2 = context.call(typed.ellipse2, radius + 1, radius)
        trimmed = context.call(typed.trim_curve2, segment, radius / 4, radius + 0.5)
        rotated = segment.rotate(radius * math.pi / 4)

        self.assertEqual(events, [])
        _assert_coordinates(self, circle.point(0).value(), (2.0, 0.0, 0.0))
        _assert_coordinates(self, ellipse.point(0).value(), (3.0, 0.0, 0.0))
        _assert_coordinates(self, line.point(3).value(), (4.0, 1.0, 1.0))
        _assert_coordinates(self, segment.point(4).value(), (4.0, 0.0))
        _assert_coordinates(self, ellipse2.point(0).value(), (3.0, 0.0))
        _assert_coordinates(self, rotated.point(4).value(), (0.0, 4.0))
        _assert_coordinates(
            self,
            tuple(float(value) for value in trimmed.range()),
            (0.5, 2.5),
        )
        self.assertTrue(events)

    def test_native_boundaries_are_owned_snapshots(self):
        context = typed.Context.deferred(cache=False)

        source = Geom_Circle(
            gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
            2,
        )
        curve = typed.Curve.from_ocp(source, context=context)
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
        curve2 = typed.Curve2.from_ocp(source2, context=context)
        self.assertIs(get_type_hints(typed.Curve2.native)["return"], Geom2d_Curve)
        source2.SetMajorRadius(8)
        first2 = curve2.native()
        first2.SetMajorRadius(7)
        self.assertEqual(curve2.native().MajorRadius(), 3.0)

        with self.assertRaisesRegex(TypeError, "Geom_Curve"):
            typed.Curve.from_ocp(source2, context=context)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "Geom2d_Curve"):
            typed.Curve2.from_ocp(source, context=context)  # type: ignore[arg-type]

    def test_invalid_inputs_fail_at_the_typed_or_resolved_boundary(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "origin must be Point3"):
            context.call(typed.line, context.call(typed.point2, 0, 0), context.call(typed.vector, 1, 0, 0))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.line, context.call(typed.point, 0, 0, 0), other.call(typed.vector, 1, 0, 0))
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.segment2, context.call(typed.point2, 0, 0), other.call(typed.point2, 1, 0))
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.trim_curve2, other.call(typed.ellipse2, 2, 1), 0, 1)

        invalid = context.call(typed.circle_curve, 0)
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            invalid.native()
        with self.assertRaisesRegex(ValueError, "non-zero Vector3"):
            context.call(typed.line, context.call(typed.point, 0, 0, 0), context.call(typed.vector, 0, 0, 0)).native()
        with self.assertRaisesRegex(ValueError, "must not be less"):
            context.call(typed.ellipse_curve, 1, 2).native()
        with self.assertRaisesRegex(ValueError, "endpoints must be distinct"):
            point = context.call(typed.point2, 0, 0)
            context.call(typed.segment2, point, point).native()
        with self.assertRaisesRegex(ValueError, "angle must be finite"):
            context.call(typed.ellipse2, 2, 1).rotate(math.inf).native()

        immediate = typed.Context.immediate(cache=False)
        with self.assertRaisesRegex(ValueError, "positive scalar"):
            immediate.call(typed.circle_curve, 0)


class TypedCurveCacheTest(unittest.TestCase):
    def test_curve_cache_uses_family_specific_non_pickle_artifacts(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.circle_curve, 2).native()

        self.assertEqual(len(store.records), 1)
        key, record = next(iter(store.records.items()))
        self.assertEqual(record.result_type_id, "zencad.typed.Curve.v2")
        self.assertEqual(
            record.serializer_id,
            "zencad.curve.occt-set-artifact.v2",
        )
        self.assertEqual(record.value.payload, b"zencad.typed.curve\x00v2")
        self.assertEqual(record.value.artifacts[0].name, "curve.geom")
        self.assertGreater(len(record.value.artifacts[0].data), 10)

        wrong_native = typed.Context.deferred(cache=False).call(typed.ellipse2, 3, 2).native()
        wrong_value = Curve2Serializer().dumps(curve_ops.curve2_from_ocp(wrong_native))
        store.records[key] = CacheRecord(
            schema=record.schema,
            result_type_id=record.result_type_id,
            serializer_id=record.serializer_id,
            value=wrong_value,
        )

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.call(typed.circle_curve, 2)
        self.assertIs(type(restored.native()), Geom_Circle)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_context_and_fresh_process_reuse_curve_cache(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.ellipse2, 3, 2).rotate(0.5).native()

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        self.assertIsInstance(
            second.call(typed.ellipse2, 3, 2).rotate(0.5).native(), Geom2d_Ellipse
        )
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
context = typed.Context.deferred(
    cache=True,
    cache_store=MappingCacheStore(DirCache_v2(sys.argv[1])),
    progress_hooks=(events.append,),
)
context.call(typed.circle_curve, 2).point(0).value()
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
