import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS_Shape
from evalcache.v2 import (
    CacheRecord,
    EvaluationEventKind,
    EvaluationMode,
    MemoryCacheStore,
)

from zencad import geom as typed
from zencad.runtime.scene_protocol import decode_brep, encode_brep


class SpyCacheStore:
    def __init__(self):
        self.records: dict[str, CacheRecord] = {}
        self.get_count = 0
        self.put_count = 0
        self.delete_count = 0

    def get(self, key: str):
        self.get_count += 1
        return self.records.get(key)

    def put(self, key: str, record: CacheRecord):
        self.put_count += 1
        self.records[key] = record

    def delete(self, key: str):
        self.delete_count += 1
        self.records.pop(key, None)

    @property
    def access_count(self):
        return self.get_count + self.put_count + self.delete_count


def representative_chain(context: typed.Context):
    outer: typed.Solid = context.call(typed.box, 10)
    inner: typed.Solid = context.call(typed.box, 4).translate(3, 3, 3)
    result: typed.Shape = outer - inner
    faces: typed.DeferredSequence[typed.Face] = result.faces()
    face: typed.Face = faces[0]
    mass: typed.Scalar = result.mass()
    center: typed.Point3 = result.center()
    offset: typed.Vector3 = typed.Vector3(mass / 1000, center.y, 0)
    moved: typed.Shape = result.translate(offset)
    return moved, face, faces, mass, center, offset


class TypedVerticalSliceTest(unittest.TestCase):
    def test_domain_classes_are_stable_across_evaluation_and_cache_policy(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    store = SpyCacheStore()
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=store,
                        progress_hooks=(events.append,),
                    )
                    moved, face, faces, mass, center, offset = representative_chain(
                        context
                    )

                    observed_types.add(
                        tuple(
                            type(value)
                            for value in (moved, face, faces, mass, center, offset)
                        )
                    )
                    self.assertIsInstance(moved, typed.Shape)
                    self.assertIsInstance(face, typed.Face)
                    self.assertIsInstance(faces, typed.DeferredSequence)
                    self.assertIsInstance(mass, typed.Scalar)
                    self.assertIsInstance(center, typed.Point3)
                    self.assertIsInstance(offset, typed.Vector3)

                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])
                        self.assertEqual(store.access_count, 0)

                    self.assertAlmostEqual(float(mass), 936.0)
                    self.assertEqual(
                        tuple(round(value, 6) for value in center.value()),
                        (5.0, 5.0, 5.0),
                    )
                    self.assertEqual(
                        tuple(round(value, 6) for value in offset.value()),
                        (0.936, 5.0, 0.0),
                    )
                    native = moved.native()
                    self.assertIsInstance(native, TopoDS_Shape)
                    self.assertFalse(native.IsNull())
                    exported = encode_brep(native)
                    self.assertFalse(decode_brep(exported).IsNull())
                    self.assertEqual(face.native().ShapeType(), TopAbs_FACE)

                    if cache:
                        self.assertGreater(store.get_count, 0)
                        self.assertGreater(store.put_count, 0)
                    else:
                        self.assertEqual(store.access_count, 0)

        self.assertEqual(len(observed_types), 1)

    def test_sequence_indexing_stays_deferred_but_len_materializes(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        faces = context.call(typed.box, 2).faces()

        face = faces[0]
        self.assertIsInstance(face, typed.Face)
        self.assertEqual(events, [])

        self.assertEqual(len(faces), 6)
        self.assertTrue(events)

    def test_shape_cache_record_contains_brep_artifact(self):
        store = MemoryCacheStore()
        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first.call(typed.box, 2).native()

        self.assertEqual(len(store.records), 1)
        record = next(iter(store.records.values()))
        self.assertEqual(record.result_type_id, "zencad.typed.Solid.v1")
        self.assertEqual(record.serializer_id, "zencad.shape.brep-artifact.v1")
        self.assertEqual(record.value.payload, b"zencad.typed.shape\x00v1")
        self.assertEqual(len(record.value.artifacts), 1)
        self.assertEqual(record.value.artifacts[0].name, "shape.brep")
        self.assertGreater(len(record.value.artifacts[0].data), 100)

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        restored = second.call(typed.box, 2).native()
        self.assertFalse(restored.IsNull())
        self.assertIn(
            EvaluationEventKind.CACHE_HIT,
            [event.kind for event in second_events],
        )

    def test_persistent_brep_cache_hits_in_a_fresh_process(self):
        script = """
import json
import sys
from collections import Counter

from evalcache import DirCache_v2
from evalcache.v2 import MappingCacheStore
from zencad import geom as typed

events = []
context = typed.Context.deferred(
    cache=True,
    cache_store=MappingCacheStore(DirCache_v2(sys.argv[1])),
    progress_hooks=(events.append,),
)
context.call(typed.box, 2).translate(1, 2, 3).native()
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

        first_counts = json.loads(first.stdout.strip().splitlines()[-1])
        second_counts = json.loads(second.stdout.strip().splitlines()[-1])
        self.assertGreater(first_counts.get("cache_store", 0), 0)
        self.assertGreater(second_counts.get("cache_hit", 0), 0)
        self.assertEqual(second_counts.get("cache_store", 0), 0)

    def test_handles_from_different_contexts_cannot_be_mixed(self):
        first = typed.Context.deferred(cache=False)
        second = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different contexts"):
            _ = first.call(typed.box, 1) - second.call(typed.box, 1)

        with self.assertRaisesRegex(ValueError, "different contexts"):
            typed.Vector3(first.call(typed.box, 1).mass(), second.call(typed.box, 1).mass(), 0)


if __name__ == "__main__":
    unittest.main()
