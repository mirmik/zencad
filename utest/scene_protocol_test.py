import importlib.util
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.TopoDS import TopoDS_Compound

import zencad
from zencad.occ_compat import add_to_bounds, volume_properties
import zencad.runtime.scene_protocol as scene_protocol
from zencad.runtime.scene_protocol import (
    FileSnapshotBundle,
    PayloadIntegrityError,
    ProtocolError,
    SceneManifest,
    SceneObjectRecord,
    SceneSnapshot,
    SupersededGenerationError,
    UnsupportedProtocolVersion,
    decode_brep,
    decode_mesh,
    decode_snapshot_frame,
    encode_brep,
    encode_mesh,
    encode_snapshot_frame,
    ensure_current_generation,
    select_snapshot_transport,
)


ROOT = Path(__file__).parents[1]


def shape_signature(shape):
    properties = GProp_GProps()
    volume_properties(shape, properties)
    bounds = Bnd_Box()
    add_to_bounds(shape, bounds)
    return properties.Mass(), bounds.Get()


def compound_of_boxes(count):
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    context = zencad.Context.immediate(cache=False)
    for index in range(count):
        box = BRepPrimAPI_MakeBox(1.0, 2.0, 3.0).Shape()
        moved = zencad.Shape.from_ocp(box, context=context).translate(
            index * 2.0, 0, 0
        ).native()
        builder.Add(compound, moved)
    return compound


def organizer_model():
    path = (
        ROOT
        / "zencad"
        / "examples"
        / "Models"
        / "organizer"
        / "organizer.py"
    )
    spec = importlib.util.spec_from_file_location("zencad_test_organizer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.organizer(3, 5, 27, 20, 64, 1.5, 5, 5).native()


class SceneProtocolTest(unittest.TestCase):
    def make_snapshot(self):
        box_payload = encode_brep(zencad.box(10))
        return SceneSnapshot(
            generation=7,
            objects=(
                SceneObjectRecord(
                    object_id="main-box",
                    kind="brep",
                    payload=box_payload,
                    properties={
                        "color": [0.1, 0.2, 0.3, 0.4],
                        "label": "форма",
                        "name": "main",
                        "visible": True,
                    },
                ),
            ),
            camera_policy="preserve",
            metadata={"source": "scene_protocol_test.py"},
        )

    def test_brep_round_trip_representative_shapes(self):
        shapes = {
            "box": zencad.box(10).native(),
            "boolean": (
                zencad.box(20, center=True) - zencad.sphere(5)
            ).native(),
            "compound": compound_of_boxes(50),
            "organizer": organizer_model(),
        }
        for name, source in shapes.items():
            with self.subTest(name=name):
                restored = decode_brep(encode_brep(source))
                source_mass, source_bounds = shape_signature(source)
                restored_mass, restored_bounds = shape_signature(restored)
                self.assertAlmostEqual(restored_mass, source_mass, places=8)
                for actual, expected in zip(restored_bounds, source_bounds):
                    self.assertAlmostEqual(actual, expected, places=8)

    def test_binary_frame_round_trip(self):
        source = self.make_snapshot()
        restored = decode_snapshot_frame(encode_snapshot_frame(source))

        self.assertEqual(restored.generation, source.generation)
        self.assertEqual(restored.camera_policy, "preserve")
        self.assertEqual(dict(restored.metadata), dict(source.metadata))
        self.assertEqual(len(restored.objects), 1)
        self.assertEqual(restored.objects[0].object_id, "main-box")
        self.assertEqual(
            dict(restored.objects[0].properties),
            dict(source.objects[0].properties),
        )
        self.assertEqual(restored.objects[0].payload, source.objects[0].payload)
        decode_brep(restored.objects[0].payload)

    def test_public_manifest_round_trip_has_no_geometry_payload(self):
        source = self.make_snapshot()
        manifest = source.manifest()
        payload = json.loads(manifest.to_json())

        self.assertEqual(payload["schema"], "zencad.scene_manifest")
        self.assertEqual(payload["objects"][0]["name"], "main")
        self.assertEqual(payload["objects"][0]["geometry"]["encoding"], "brep")
        self.assertNotIn("payload", payload["objects"][0])
        self.assertEqual(SceneManifest.from_dict(payload), manifest)

    def test_mesh_payload_round_trip_and_validation(self):
        source = zencad.to_mesh(zencad.box(2))
        restored = decode_mesh(encode_mesh(source))

        self.assertEqual(tuple(restored.positions), source.positions)
        self.assertEqual(tuple(restored.normals), source.normals)
        self.assertEqual(tuple(restored.triangles), source.triangles)
        self.assertEqual(restored.triangle_face_ids, [])

        corrupt = bytearray(encode_mesh(source))
        corrupt[-1] ^= 0x01
        with self.assertRaisesRegex(PayloadIntegrityError, "geometry"):
            decode_mesh(bytes(corrupt))
        with self.assertRaises(PayloadIntegrityError):
            decode_mesh(b"short")

    def test_file_bundle_round_trip_and_atomic_target(self):
        source = self.make_snapshot()
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "generation-7"
            FileSnapshotBundle.write(path, source)
            restored = FileSnapshotBundle.read(path)
            self.assertEqual(restored, source)
            self.assertTrue((path / "manifest.json").is_file())
            self.assertTrue((path / "payload-000000.bin").is_file())
            with self.assertRaises(FileExistsError):
                FileSnapshotBundle.write(path, source)

    def test_corrupt_binary_payload_is_rejected(self):
        frame = bytearray(encode_snapshot_frame(self.make_snapshot()))
        frame[-1] ^= 0x01
        with self.assertRaisesRegex(
            PayloadIntegrityError, "digest mismatch"
        ):
            decode_snapshot_frame(bytes(frame))

    def test_corrupt_file_payload_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "generation-7"
            FileSnapshotBundle.write(path, self.make_snapshot())
            payload_path = path / "payload-000000.bin"
            payload = bytearray(payload_path.read_bytes())
            payload[-1] ^= 0x01
            payload_path.write_bytes(payload)
            with self.assertRaisesRegex(
                PayloadIntegrityError, "digest mismatch"
            ):
                FileSnapshotBundle.read(path)

    def test_unknown_frame_version_is_rejected(self):
        frame = bytearray(encode_snapshot_frame(self.make_snapshot()))
        struct.pack_into(">H", frame, 4, 99)
        with self.assertRaisesRegex(
            UnsupportedProtocolVersion, "version 99"
        ):
            decode_snapshot_frame(bytes(frame))

    def test_unknown_bundle_version_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "generation-7"
            FileSnapshotBundle.write(path, self.make_snapshot())
            manifest_path = path / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["protocol_version"] = 99
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                UnsupportedProtocolVersion, "version 99"
            ):
                FileSnapshotBundle.read(path)

    def test_truncated_frame_is_rejected(self):
        frame = encode_snapshot_frame(self.make_snapshot())
        with self.assertRaises(ProtocolError):
            decode_snapshot_frame(frame[:-10])

    def test_superseded_generation_is_rejected(self):
        snapshot = self.make_snapshot()
        ensure_current_generation(snapshot, 7)
        with self.assertRaisesRegex(
            SupersededGenerationError, "not current"
        ):
            ensure_current_generation(snapshot, 8)

    def test_large_snapshot_selects_file_bundle(self):
        snapshot = self.make_snapshot()
        frame_size = len(encode_snapshot_frame(snapshot))
        self.assertEqual(select_snapshot_transport(snapshot), "inline")
        with mock.patch.object(
            scene_protocol, "INLINE_FRAME_LIMIT", frame_size - 1
        ):
            self.assertEqual(select_snapshot_transport(snapshot), "file")
            with self.assertRaisesRegex(ProtocolError, "inline frame limit"):
                encode_snapshot_frame(snapshot)

    def test_invalid_brep_is_rejected(self):
        with self.assertRaisesRegex(PayloadIntegrityError, "Invalid BREP"):
            decode_brep(b"not a BREP")

    def test_invalid_record_and_generation_types_are_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "object ID"):
            SceneObjectRecord(7, "brep", b"payload")
        with self.assertRaisesRegex(ProtocolError, "object kind"):
            SceneObjectRecord("object", None, b"payload")
        with self.assertRaisesRegex(ProtocolError, "non-negative"):
            SceneSnapshot(True, ())


if __name__ == "__main__":
    unittest.main()
