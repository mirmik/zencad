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
from OCP.Poly import Poly_Triangulation
from OCP.gp import gp_Pnt

from zencad import _typed as typed
from zencad.runtime.scene_protocol import decode_mesh


class TypedMeshDataTest(unittest.TestCase):
    def test_module_declarations_match_domain_and_runtime_entry_points(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        shape = runtime.box(2)
        face = runtime.rectangle(2, 3)

        direct_mesh = typed.to_mesh(shape)
        direct_face_mesh = typed.triangulate(face)
        self.assertEqual(events, [])
        self.assertEqual(direct_mesh.value(), shape.to_mesh().value())
        self.assertEqual(direct_face_mesh.value(), face.triangulate().value())
        self.assertEqual(
            typed.mesh_boundbox(direct_mesh).value(),
            direct_mesh.boundbox().value(),
        )
        self.assertEqual(typed.get_nodes(direct_mesh), direct_mesh.get_nodes())
        self.assertEqual(
            typed.get_triangles(direct_mesh),
            direct_mesh.get_triangles(),
        )
        native = typed.mesh_to_poly_triangulation(direct_mesh)
        self.assertEqual(typed.get_nodes(native), direct_mesh.positions)
        self.assertEqual(typed.get_triangles(native), direct_mesh.triangles)
        self.assertEqual(
            typed.mesh_display_payload(direct_mesh),
            direct_mesh.display_payload(),
        )

        with self.assertRaisesRegex(TypeError, "to_mesh expects Shape"):
            typed.to_mesh(direct_mesh)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "triangulate expects Face"):
            typed.triangulate(shape)  # type: ignore[arg-type]

    def test_shape_and_face_meshes_are_policy_independent(self):
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
                    mesh = runtime.box(2).to_mesh()
                    face_mesh = runtime.rectangle(2, 3).triangulate()
                    observed.add((type(mesh), type(face_mesh)))
                    self.assertIs(type(mesh), typed.MeshData)
                    self.assertIs(type(face_mesh), typed.MeshData)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    record = mesh.value()
                    self.assertIs(type(record), typed.MeshDataRecord)
                    self.assertIs(type(record.positions), tuple)
                    self.assertIs(type(record.positions[0]), tuple)
                    self.assertIs(type(record.triangles), tuple)
                    self.assertEqual(record.vertex_count, 24)
                    self.assertEqual(record.triangle_count, 12)
                    self.assertEqual(len(record.triangle_face_ids), 12)
                    self.assertEqual(record.dropped_triangles, 0)
                    self.assertEqual(face_mesh.vertex_count, 4)
                    self.assertEqual(face_mesh.triangle_count, 2)
                    self.assertEqual(face_mesh.triangle_face_ids, (0, 0))
                    self.assertEqual(
                        mesh.boundbox().value().maximum,
                        (2.0, 2.0, 2.0),
                    )
                    self.assertIs(mesh.unlazy(), mesh)

                    with self.assertRaises(FrozenInstanceError):
                        record.dropped_triangles = 1  # type: ignore[misc]

        self.assertEqual(observed, {(typed.MeshData, typed.MeshData)})

    def test_shape_graph_is_retained_until_mesh_materialization(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        seed = runtime.box(2)
        offset = seed.mass() / 8
        mesh = seed.translate(offset, 2, 3).to_mesh(
            linear_deflection=0.25,
            angular_deflection=0.4,
        )
        bounds = mesh.boundbox()

        self.assertEqual(events, [])
        self.assertIs(type(mesh), typed.MeshData)
        for actual, expected in zip(bounds.minimum.value(), (1.0, 2.0, 3.0)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(bounds.maximum.value(), (3.0, 4.0, 5.0)):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(events)

    def test_data_numpy_and_native_boundaries_own_their_snapshots(self):
        runtime = typed.Runtime.deferred(cache=False)
        positions = [[0.123456789012345, 0, 0], [1, 0, 0], [0, 1, 0]]
        normals = [[0, 0, 1], [0, 0, 1], [0, 0, 1]]
        triangles = [[0, 1, 2]]
        face_ids = [7]
        mesh = typed.MeshData.from_data(
            positions,
            normals,
            triangles,
            face_ids,
            runtime=runtime,
            dropped_triangles=2,
        )
        positions[0][0] = 9
        normals[0][2] = -1
        triangles[0][0] = 2
        face_ids[0] = 99

        self.assertEqual(mesh.positions[0][0], 0.123456789012345)
        self.assertEqual(mesh.normals[0], (0.0, 0.0, 1.0))
        self.assertEqual(mesh.triangles, ((0, 1, 2),))
        self.assertEqual(mesh.triangle_face_ids, (7,))
        self.assertEqual(mesh.dropped_triangles, 2)

        arrays = mesh.to_numpy()
        self.assertIs(type(arrays), typed.MeshArrayRecord)
        arrays.positions[0, 0] = 8
        arrays.triangles[0, 0] = 2
        self.assertEqual(mesh.to_numpy().positions[0, 0], 0.123456789012345)
        self.assertEqual(mesh.to_numpy().triangles[0, 0], 0)

        native = mesh.native()
        self.assertIs(type(native), Poly_Triangulation)
        native.SetNode(1, gp_Pnt(10, 10, 10))
        self.assertEqual(mesh.native().Node(1).X(), 0.123456789012345)

    def test_display_payload_is_the_explicit_scene_transport_boundary(self):
        runtime = typed.Runtime.deferred(cache=False)
        mesh = runtime.box(2).to_mesh()

        restored = decode_mesh(mesh.display_payload())

        self.assertEqual(tuple(restored.positions), mesh.positions)
        self.assertEqual(tuple(restored.normals), mesh.normals)
        self.assertEqual(tuple(restored.triangles), mesh.triangles)
        self.assertEqual(restored.triangle_face_ids, [])

    def test_invalid_data_and_meshing_options_are_rejected(self):
        runtime = typed.Runtime.deferred(cache=False)
        valid_positions = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        valid_normals = ((0, 0, 1),) * 3
        valid_triangles = ((0, 1, 2),)

        invalid_cases = (
            ((), valid_normals, valid_triangles, (0,)),
            (valid_positions, ((0, 0, 0),) * 3, valid_triangles, (0,)),
            (valid_positions, valid_normals, ((0, 0, 3),), (0,)),
            (valid_positions, valid_normals, valid_triangles, ()),
            (valid_positions, valid_normals, valid_triangles, (-1,)),
        )
        for positions, normals, triangles, face_ids in invalid_cases:
            with self.subTest(data=(positions, normals, triangles, face_ids)):
                with self.assertRaises(ValueError):
                    typed.MeshData.from_data(
                        positions,
                        normals,
                        triangles,
                        face_ids,
                        runtime=runtime,
                    )

        with self.assertRaises(ValueError):
            typed.MeshData.from_data(
                valid_positions,
                valid_normals,
                valid_triangles,
                (0,),
                runtime=runtime,
                dropped_triangles=-1,
            )
        with self.assertRaisesRegex(ValueError, "linear_deflection"):
            runtime.box(1).to_mesh(0)
        with self.assertRaisesRegex(ValueError, "angular_deflection"):
            runtime.box(1).to_mesh(0.1, float("inf"))
        with self.assertRaisesRegex(ValueError, "crease_angle"):
            runtime.box(1).to_mesh(crease_angle=-1)
        with self.assertRaisesRegex(TypeError, "must be bool"):
            runtime.box(1).to_mesh(relative=1)  # type: ignore[arg-type]


class TypedMeshCacheTest(unittest.TestCase):
    def test_cache_uses_full_fidelity_binary_artifact_and_rejects_corruption(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        source = first.box(2).to_mesh()
        source.value()

        key, record = next(
            (key, record)
            for key, record in store.records.items()
            if record.result_type_id == "zencad.typed.MeshData.v1"
        )
        self.assertEqual(record.serializer_id, "zencad.mesh.binary-artifact.v1")
        self.assertEqual(record.value.payload, b"zencad.typed.mesh\x00v1")
        self.assertEqual(record.value.artifacts[0].name, "mesh.bin")
        self.assertTrue(record.value.artifacts[0].data.startswith(b"ZCTM"))

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
        restored = second.box(2).to_mesh()
        self.assertEqual(restored.triangle_face_ids, source.triangle_face_ids)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_fresh_runtime_and_process_reuse_mesh_cache(self):
        store = MemoryCacheStore()
        first = typed.Runtime.deferred(cache=True, cache_store=store)
        first.rectangle(2, 3).triangulate().value()

        events = []
        second = typed.Runtime.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.rectangle(2, 3).triangulate().value()
        self.assertEqual(restored.triangle_face_ids, (0, 0))
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
runtime.box(2).to_mesh().value()
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
