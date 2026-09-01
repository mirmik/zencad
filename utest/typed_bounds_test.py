import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from evalcache.v2 import (
    CacheRecord,
    EvaluationEventKind,
    EvaluationMode,
    MemoryCacheStore,
    SerializedValue,
)
from OCP.Bnd import Bnd_Box

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_context


def _assert_coordinates(
    testcase: unittest.TestCase,
    actual: tuple[float, ...],
    expected: tuple[float, ...],
) -> None:
    testcase.assertEqual(len(actual), len(expected))
    for left, right in zip(actual, expected):
        testcase.assertAlmostEqual(left, right, places=6)


class TypedBoundaryBoxTest(unittest.TestCase):
    def test_boundary_box_family_is_declared_at_module_level(self):
        self.assertIsInstance(typed.boundary_box, DomainOperation)
        self.assertIsInstance(typed.empty_boundary_box, DomainOperation)
        self.assertIsInstance(typed.boundbox, DomainOperation)

        context = typed.Context.deferred(cache=False)
        seed = context.call(typed.box, 2)
        minimum = seed.center()
        maximum = minimum + context.call(typed.vector3, 1, 2, 3)
        with using_context(context):
            bounds = typed.boundary_box(minimum, maximum)
            empty = typed.empty_boundary_box()
            shape_bounds = typed.boundbox(seed)

        self.assertIs(bounds.context, context)
        self.assertIs(empty.context, context)
        self.assertIs(shape_bounds.context, context)
        self.assertEqual(
            bounds._state.operation_id,
            "zencad.typed.boundary-box.from-points",
        )
        self.assertEqual(
            shape_bounds._state.operation_id, "zencad.typed.shape.boundbox"
        )
        self.assertEqual(
            bounds.minimum._state.operation_id, "zencad.typed.boundary-box.minimum"
        )
        self.assertEqual(
            bounds.maximum._state.operation_id, "zencad.typed.boundary-box.maximum"
        )
        self.assertEqual(
            bounds.size._state.operation_id, "zencad.typed.boundary-box.size"
        )
        self.assertEqual(
            bounds.center._state.operation_id, "zencad.typed.boundary-box.center"
        )
        self.assertEqual(
            bounds.xmin._state.operation_id, "zencad.typed.boundary-box.coordinate"
        )

    def test_shape_bounds_are_policy_independent_structured_handles(self):
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
                    bounds = (
                        context.call(typed.box, 2, 3, 4).translate(-1, 2, 5).boundbox()
                    )
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

                    with self.assertRaises(FrozenInstanceError):
                        record.xmin = 10  # type: ignore[misc]

        self.assertEqual(observed_types, {typed.BoundaryBox})

    def test_bbox_alias_and_context_factory_preserve_the_graph(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = context.call(typed.box, 2)
        minimum = seed.center()
        extent = seed.mass() / 4
        maximum = minimum + context.call(typed.vector, extent, extent + 1, extent + 2)
        explicit = context.call(typed.boundary_box, minimum, maximum)
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
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        first = context.call(
            typed.boundary_box,
            context.call(typed.point3, 1, 2, 3),
            context.call(typed.point3, 4, 6, 8),
        )
        second = context.call(typed.box, 1).boundbox()
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
        context = typed.Context.deferred(cache=False)
        empty = (context.call(typed.box, 1) - context.call(typed.box, 1)).boundbox()
        nonempty = context.call(typed.box, 2).boundbox()

        self.assertTrue(empty.is_empty())
        self.assertTrue(empty.native().IsVoid())
        self.assertTrue(
            context.call(
                typed.empty_boundary_box,
            ).is_empty()
        )
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
        context = typed.Context.deferred(cache=False)
        source = Bnd_Box()
        source.Update(0.123456789012345, 2, 3, 4.123456789012345, 5, 6)
        bounds = typed.BoundaryBox.from_ocp(source, context=context)
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
        self.assertTrue(typed.BoundaryBox.from_ocp(void, context=context).is_empty())
        with self.assertRaisesRegex(TypeError, "Bnd_Box"):
            typed.BoundaryBox.from_ocp(object(), context=context)  # type: ignore[arg-type]

    def test_invalid_factory_inputs_are_rejected(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaises(TypeError):
            context.call(
                typed.boundary_box,
                context.call(typed.point2, 0, 0),
                context.call(typed.point, 1, 1, 1),
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.boundary_box,
                context.call(typed.point, 0, 0, 0),
                other.call(typed.point, 1, 1, 1),
            )
        with self.assertRaisesRegex(ValueError, "minimum exceeds maximum"):
            context.call(
                typed.boundary_box,
                context.call(typed.point, 2, 0, 0),
                context.call(typed.point, 1, 1, 1),
            )
        with self.assertRaises(TypeError):
            context.call(typed.empty_boundary_box).union(
                context.call(typed.box, 1)  # type: ignore[arg-type]
            ).value()
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(
                typed.empty_boundary_box,
            ).union(
                other.call(
                    typed.empty_boundary_box,
                )
            )

    def test_curve_and_surface_ranges_are_named_graph_records(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        curve_range = context.call(
            typed.circle_curve, context.call(typed.box, 2).mass() / 4
        ).range()
        surface_range = context.call(typed.cylinder_surface, 2).u_range()

        self.assertIs(type(curve_range), typed.Interval)
        self.assertIs(type(curve_range.lower), typed.Scalar)
        self.assertIs(type(curve_range.upper), typed.Scalar)
        self.assertIs(type(surface_range), typed.Interval)
        self.assertEqual(events, [])
        self.assertAlmostEqual(curve_range.lower.value(), 0.0)
        self.assertAlmostEqual(curve_range.length().value(), 2 * 3.141592653589793)
        self.assertEqual(tuple(curve_range), (curve_range.lower, curve_range.upper))
        self.assertTrue(events)


class TypedBoundaryBoxCacheTest(unittest.TestCase):
    def test_cache_is_binary_non_pickle_and_rejects_invalid_payload(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.box, 2).boundbox().value()

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
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        self.assertFalse(second.call(typed.box, 2).boundbox().is_empty())
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_context_and_process_reuse_boundary_box_cache(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.box, 2).boundbox().value()

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        second.call(typed.box, 2).boundbox().value()
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
context.call(typed.box, 2).boundbox().value()
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
