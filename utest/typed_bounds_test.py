from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evalcache.v2 import (
    CacheRecord,
    EvaluationEventKind,
    EvaluationMode,
    MemoryCacheStore,
    SerializedValue,
)
from OCP.Bnd import Bnd_Box

from zencad import _typed as typed


def _assert_coordinates(
    testcase: unittest.TestCase,
    actual: tuple[float, ...],
    expected: tuple[float, ...],
) -> None:
    testcase.assertEqual(len(actual), len(expected))
    for left, right in zip(actual, expected):
        testcase.assertAlmostEqual(left, right, places=6)


class TypedBoundaryBoxTest(unittest.TestCase):
    def test_shape_bounds_are_policy_independent_structured_handles(self):
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
                    bounds = runtime.box(2, 3, 4).translate(-1, 2, 5).boundbox()
                    observed_types.add(type(bounds))
                    self.assertIs(type(bounds), typed.BoundaryBox)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    record = bounds.value()
                    self.assertIs(type(record), typed.BoundaryBoxRecord)
                    _assert_coordinates(self, record.minimum, (-1.0, 2.0, 5.0))
                    _assert_coordinates(self, record.maximum, (1.0, 5.0, 9.0))
                    _assert_coordinates(self, bounds.minimum.value(), record.minimum)
                    _assert_coordinates(self, bounds.maximum.value(), record.maximum)
                    _assert_coordinates(self, bounds.size.value(), (2.0, 3.0, 4.0))
                    _assert_coordinates(self, bounds.center.value(), (0.0, 3.5, 7.0))
                    self.assertIs(type(bounds.x_range()), typed.Interval)
                    _assert_coordinates(self, bounds.x_range().value(), (-1.0, 1.0))
                    self.assertAlmostEqual(bounds.y_range().length().value(), 3.0, 6)
                    self.assertAlmostEqual(bounds.z_range().length().value(), 4.0, 6)
                    self.assertFalse(bounds.is_empty())
                    self.assertFalse(bounds.native().IsVoid())
                    self.assertIs(bounds.unlazy(), bounds)

                    with self.assertRaises(FrozenInstanceError):
                        record.xmin = 10  # type: ignore[misc]

        self.assertEqual(observed_types, {typed.BoundaryBox})

    def test_bbox_alias_and_runtime_factory_preserve_the_graph(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = runtime.box(2)
        minimum = seed.center()
        extent = seed.mass() / 4
        maximum = minimum + runtime.vector(extent, extent + 1, extent + 2)
        explicit = runtime.boundary_box(minimum, maximum)
        shape_bounds = seed.translate(extent, 0, 0).bbox()
        combined = explicit.union(shape_bounds)

        self.assertEqual(events, [])
        self.assertIs(type(explicit), typed.BoundaryBox)
        self.assertEqual(explicit.minimum.value(), (1.0, 1.0, 1.0))
        _assert_coordinates(self, explicit.maximum.value(), (3.0, 4.0, 5.0))
        _assert_coordinates(self, combined.value().minimum, (1.0, 0.0, 0.0))
        _assert_coordinates(self, combined.value().maximum, (4.0, 4.0, 5.0))
        self.assertTrue(events)

    def test_legacy_accessors_and_shape_keep_immutable_typed_contract(self):
        events = []
        runtime = typed.Runtime.deferred(cache=False, progress_hooks=(events.append,))
        first = runtime.boundary_box(runtime.point3(1, 2, 3), runtime.point3(4, 6, 8))
        second = runtime.box(1).boundbox()
        combined = first.add(second)
        shape = first.shape()

        self.assertIs(type(combined), typed.BoundaryBox)
        self.assertIs(type(shape), typed.Solid)
        self.assertEqual(events, [])
        self.assertEqual(first.xrange().value(), (1.0, 4.0))
        self.assertEqual(first.yrange().value(), (2.0, 6.0))
        self.assertEqual(first.zrange().value(), (3.0, 8.0))
        self.assertEqual(float(first.xlength()), 3.0)
        self.assertEqual(float(first.ylength()), 4.0)
        self.assertEqual(float(first.zlength()), 5.0)
        shape_record = shape.boundbox().value()
        first_record = first.value()
        _assert_coordinates(self, shape_record.minimum, first_record.minimum)
        _assert_coordinates(self, shape_record.maximum, first_record.maximum)
        self.assertEqual(first.value().minimum, (1.0, 2.0, 3.0))
        self.assertTrue(events)

    def test_empty_bounds_are_explicit_and_union_identity(self):
        runtime = typed.Runtime.deferred(cache=False)
        empty = (runtime.box(1) - runtime.box(1)).boundbox()
        nonempty = runtime.box(2).boundbox()

        self.assertTrue(empty.is_empty())
        self.assertTrue(empty.native().IsVoid())
        self.assertTrue(runtime.empty_boundary_box().is_empty())
        self.assertEqual(empty.union(nonempty).value(), nonempty.value())
        self.assertEqual(nonempty.union(empty).value(), nonempty.value())

        with self.assertRaisesRegex(ValueError, "no materialized record"):
            empty.value()
        with self.assertRaisesRegex(ValueError, "no corner points"):
            empty.minimum.value()
        with self.assertRaisesRegex(ValueError, "no size"):
            empty.size.value()
        with self.assertRaisesRegex(ValueError, "no coordinates"):
            empty.xmin.value()

    def test_native_boundary_is_an_owned_snapshot(self):
        runtime = typed.Runtime.deferred(cache=False)
        source = Bnd_Box()
        source.Update(0.123456789012345, 2, 3, 4.123456789012345, 5, 6)
        bounds = typed.BoundaryBox.from_ocp(source, runtime=runtime)
        source.Update(-10, -10, -10, 10, 10, 10)

        first = bounds.native()
        first.Update(-20, -20, -20, 20, 20, 20)
        record = bounds.value()
        self.assertEqual(record.xmin, 0.123456789012345)
        self.assertEqual(record.xmax, 4.123456789012345)
        self.assertEqual(
            bounds.native().Get(), (record.xmin, 2.0, 3.0, record.xmax, 5.0, 6.0)
        )

        void = Bnd_Box()
        self.assertTrue(typed.BoundaryBox.from_ocp(void, runtime=runtime).is_empty())
        with self.assertRaisesRegex(TypeError, "Bnd_Box"):
            typed.BoundaryBox.from_ocp(object(), runtime=runtime)  # type: ignore[arg-type]

    def test_invalid_factory_inputs_are_rejected(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "Point3 corners"):
            runtime.boundary_box(runtime.point2(0, 0), runtime.point(1, 1, 1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.boundary_box(runtime.point(0, 0, 0), other.point(1, 1, 1))
        with self.assertRaisesRegex(ValueError, "minimum exceeds maximum"):
            runtime.boundary_box(runtime.point(2, 0, 0), runtime.point(1, 1, 1))
        with self.assertRaisesRegex(TypeError, "expects BoundaryBox"):
            runtime.empty_boundary_box().union(runtime.box(1))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.empty_boundary_box().union(other.empty_boundary_box())

    def test_curve_and_surface_ranges_are_named_graph_records(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        curve_range = runtime.circle_curve(runtime.box(2).mass() / 4).range()
        surface_range = runtime.cylinder_surface(2).u_range()

        self.assertIs(type(curve_range), typed.Interval)
        self.assertIs(type(curve_range.lower), typed.Scalar)
        self.assertIs(type(curve_range.upper), typed.Scalar)
        self.assertIs(type(surface_range), typed.Interval)
        self.assertEqual(events, [])
        self.assertAlmostEqual(curve_range.lower.value(), 0.0)
        self.assertAlmostEqual(curve_range.length().value(), 2 * 3.141592653589793)
        self.assertEqual(tuple(curve_range), (curve_range.lower, curve_range.upper))
        self.assertIs(curve_range.unlazy(), curve_range)
        self.assertTrue(events)


class TypedBoundaryBoxCacheTest(unittest.TestCase):
    def test_cache_is_binary_non_pickle_and_rejects_invalid_payload(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.box(2).boundbox().value()

        key, record = next(
            (key, record)
            for key, record in store.records.items()
            if record.result_type_id == "zencad.typed.BoundaryBox.v1"
        )
        self.assertEqual(record.serializer_id, "zencad.boundary-box.struct.v1")
        self.assertTrue(
            record.value.payload.startswith(b"zencad.typed.boundary-box\x00v1\x00B")
        )
        self.assertEqual(record.value.artifacts, ())

        store.records[key] = CacheRecord(
            schema=record.schema,
            result_type_id=record.result_type_id,
            serializer_id=record.serializer_id,
            value=SerializedValue(payload=b"zencad.typed.surface\x00v1"),
        )
        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        self.assertFalse(second.box(2).boundbox().is_empty())
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_runtime_and_process_reuse_boundary_box_cache(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.box(2).boundbox().value()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        second.box(2).boundbox().value()
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
runtime.box(2).boundbox().value()
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
