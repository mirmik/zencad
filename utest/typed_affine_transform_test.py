import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
from evalcache.v2 import (
    CacheRecord,
    EvaluationMode,
    Expression,
)

from zencad import _typed as typed


TOLERANCE = 1e-11


class SpyStore:
    def __init__(self):
        self.records: dict[str, CacheRecord] = {}
        self.reads = 0
        self.writes = 0
        self.deletes = 0

    def get(self, key: str):
        self.reads += 1
        return self.records.get(key)

    def put(self, key: str, record: CacheRecord):
        self.writes += 1
        self.records[key] = record

    def delete(self, key: str):
        self.deletes += 1
        self.records.pop(key, None)


class TypedAffineTransformTest(unittest.TestCase):
    def assertCoordinatesAlmostEqual(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected, strict=True)):
            self.assertAlmostEqual(
                actual_item,
                expected_item,
                delta=TOLERANCE,
                msg=f"coordinate {index}: {actual!r} != {expected!r}",
            )

    def assertMatricesAlmostEqual(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_row, expected_row in zip(actual, expected, strict=True):
            self.assertCoordinatesAlmostEqual(actual_row, expected_row)

    def test_result_classes_are_policy_independent(self):
        observed_types = set()
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    store = SpyStore()
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=store,
                    )
                    shape = runtime.box(2)
                    factor = shape.mass() / 4
                    affine = runtime.scaleXYZ(factor, 2, 3)
                    point = affine(shape.center())
                    vector = affine(runtime.vector(1, 2, 3))
                    moved = shape.transform(affine)
                    observed_types.add(
                        tuple(
                            type(value)
                            for value in (
                                affine,
                                affine.translation,
                                affine.determinant,
                                point,
                                vector,
                                moved,
                            )
                        )
                    )
                    self.assertEqual(type(affine), typed.AffineTransform)
                    self.assertEqual(type(point), typed.Point3)
                    self.assertEqual(type(vector), typed.Vector3)
                    self.assertEqual(type(moved), typed.Solid)
                    self.assertFalse(moved.native().IsNull())

        self.assertEqual(len(observed_types), 1)

    def test_general_matrix_applies_shear_and_translation(self):
        runtime = typed.Runtime.deferred(cache=False)
        affine = runtime.affine(
            (
                (1, 0.5, 0, 10),
                (0, 2, 0.25, -3),
                (0, 0, 3, 7),
            )
        )

        self.assertCoordinatesAlmostEqual(
            affine(runtime.point(2, 4, 6)).value(),
            (14.0, 6.5, 25.0),
        )
        self.assertCoordinatesAlmostEqual(
            affine(runtime.vector(2, 4, 6)).value(),
            (4.0, 9.5, 18.0),
        )
        self.assertCoordinatesAlmostEqual(affine.translation.value(), (10, -3, 7))
        self.assertAlmostEqual(float(affine.determinant), 6.0, delta=TOLERANCE)
        self.assertMatricesAlmostEqual(
            affine.matrix(),
            (
                (1, 0.5, 0, 10),
                (0, 2, 0.25, -3),
                (0, 0, 3, 7),
                (0, 0, 0, 1),
            ),
        )

    def test_composition_inverse_and_similarity_promotion(self):
        runtime = typed.Runtime.deferred(cache=False)
        affine = runtime.affine(
            (
                (2, 0.25, 0, 1),
                (0, 3, 0.5, -2),
                (0, 0, 4, 5),
            )
        )
        similarity = runtime.translation(7, 8, 9) * runtime.rotateZ(math.pi / 3)
        point = runtime.point(2, -1, 0.5)
        vector = runtime.vector(-3, 2, 4)

        outer_similarity = similarity * affine
        outer_affine = affine * similarity
        self.assertIs(type(outer_similarity), typed.AffineTransform)
        self.assertIs(type(outer_affine), typed.AffineTransform)
        self.assertCoordinatesAlmostEqual(
            outer_similarity(point).value(),
            similarity(affine(point)).value(),
        )
        self.assertCoordinatesAlmostEqual(
            outer_affine(point).value(),
            affine(similarity(point)).value(),
        )
        self.assertCoordinatesAlmostEqual(
            affine.then(similarity)(point).value(),
            outer_similarity(point).value(),
        )
        self.assertCoordinatesAlmostEqual(
            affine.inverse()(affine(point)).value(),
            point.value(),
        )
        self.assertCoordinatesAlmostEqual(
            affine.inverse()(affine(vector)).value(),
            vector.value(),
        )
        self.assertEqual(
            typed.AffineTransform.from_transform(similarity).matrix(),
            similarity.to_affine().matrix(),
        )

    def test_non_uniform_scale_compatibility_and_shape_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        center = runtime.point(1, 2, 3)
        affine = typed.AffineTransform.scaleXYZ(
            2,
            3,
            4,
            runtime=runtime,
            center=center,
        )
        self.assertIs(typed.GeneralTransformation, typed.AffineTransform)
        self.assertCoordinatesAlmostEqual(affine(center).value(), center.value())
        self.assertCoordinatesAlmostEqual(
            affine(runtime.point(2, 4, 6)).value(),
            (3, 8, 15),
        )

        shape = runtime.box(1, 2, 3)
        scaled = shape.scaleXYZ(2, 3, 4)
        self.assertIs(type(scaled), typed.Solid)
        self.assertAlmostEqual(float(scaled.mass()), 144.0, delta=1e-8)
        self.assertCoordinatesAlmostEqual(scaled.center().value(), (1, 3, 6))
        self.assertAlmostEqual(
            float(shape.scaleX(2).mass()),
            12.0,
            delta=1e-8,
        )
        self.assertAlmostEqual(
            float(shape.scaleY(3).mass()),
            18.0,
            delta=1e-8,
        )
        self.assertAlmostEqual(
            float(shape.scaleZ(4).mass()),
            24.0,
            delta=1e-8,
        )

    def test_ocp_round_trip_returns_fresh_mutable_values(self):
        runtime = typed.Runtime.deferred(cache=False)
        native = gp_GTrsf()
        native.SetVectorialPart(gp_Mat(2, 0.5, 0, 0, 3, 0.25, 0, 0, 4))
        native.SetTranslationPart(gp_XYZ(5, -6, 7))
        affine = typed.AffineTransform.from_ocp(native, runtime=runtime)

        first = affine.to_ocp()
        second = affine.to_ocp()
        self.assertIsInstance(first, gp_GTrsf)
        self.assertIsNot(first, second)
        first.SetTranslationPart(gp_XYZ(99, 98, 97))
        self.assertCoordinatesAlmostEqual(
            (
                second.TranslationPart().X(),
                second.TranslationPart().Y(),
                second.TranslationPart().Z(),
            ),
            (5, -6, 7),
        )
        self.assertMatricesAlmostEqual(
            typed.AffineTransform.from_ocp(second, runtime=runtime).matrix(),
            affine.matrix(),
        )

    def test_cache_uses_explicit_affine_serializer_and_fresh_process(self):
        store = SpyStore()
        events = []
        runtime = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        factor = runtime.box(2).mass() / 4
        affine = runtime.scaleXYZ(factor, 2, 3)
        self.assertAlmostEqual(float(affine.determinant), 12.0, delta=TOLERANCE)

        records = [
            record for record in store.records.values() if record.result_type_id == "zencad.typed.AffineTransform.v1"
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0].serializer_id,
            "zencad.affine-transform.struct.v1",
        )
        self.assertTrue(records[0].value.payload.startswith(b"zencad.typed.affine-transform\x00v1\x00"))
        self.assertEqual(records[0].value.artifacts, ())

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
factor = runtime.box(2).mass() / 4
print(float(runtime.scaleXYZ(factor, 2, 3).determinant))
print(json.dumps(Counter(event.kind.value for event in events)))
"""
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            roots = [
                str(Path(__file__).resolve().parents[1]),
                str(Path(__file__).resolve().parents[2] / "evalcache"),
            ]
            environment["PYTHONPATH"] = os.pathsep.join(roots + [environment.get("PYTHONPATH", "")])
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

    def test_invalid_inputs_and_runtime_mixing_fail_explicitly(self):
        runtime = typed.Runtime.deferred(cache=False)
        other = typed.Runtime.deferred(cache=False)
        singular = runtime.affine(((0, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)))

        with self.assertRaisesRegex(ValueError, "3x4"):
            runtime.affine(((1, 0), (0, 1)))
        with self.assertRaisesRegex(ValueError, "finite"):
            runtime.affine(((math.nan, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)))
        with self.assertRaisesRegex(ValueError, "singular"):
            singular.inverse()
        with self.assertRaisesRegex(TypeError, "Point3 or Vector3"):
            runtime.scaleX(2).apply(runtime.point2(1, 2))
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            _ = runtime.scaleX(2) * other.scaleY(3)
        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            runtime.box(1).transform(other.scaleZ(4))
        with self.assertRaisesRegex(TypeError, "gp_GTrsf"):
            typed.AffineTransform.from_ocp(object(), runtime=runtime)

        deferred_factor = runtime.box(1).mass() - runtime.box(1).mass()
        deferred_singular = runtime.scaleX(deferred_factor)
        self.assertIsInstance(deferred_singular._state, Expression)
        with self.assertRaisesRegex(ValueError, "singular"):
            deferred_singular.inverse().matrix()


if __name__ == "__main__":
    unittest.main()
