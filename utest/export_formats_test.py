import io
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree
from zipfile import ZipFile

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.RWStl import RWStl
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Shell, TopoDS_Solid

import zencad
from zencad import geom as typed
from zencad._native.shape import Shape as ResolvedShape
from zencad._native.validation import ShapeValidationError
from zencad.occ_compat import as_face
from zencad.runtime.scene_protocol import encode_brep


def _open_solid() -> TopoDS_Solid:
    builder = BRep_Builder()
    box = BRepPrimAPI_MakeBox(2, 2, 2).Solid()
    explorer = TopExp_Explorer(box, TopAbs_FACE)
    shell = TopoDS_Shell()
    builder.MakeShell(shell)
    builder.Add(shell, as_face(explorer.Current()))
    solid = TopoDS_Solid()
    builder.MakeSolid(solid)
    builder.Add(solid, shell)
    return solid


def _stl_bounds(path: Path) -> tuple[float, float, float, float, float, float]:
    mesh = RWStl.ReadFile_s(str(path))
    coordinates = [
        (mesh.Node(index).X(), mesh.Node(index).Y(), mesh.Node(index).Z())
        for index in range(1, mesh.NbNodes() + 1)
    ]
    xs, ys, zs = zip(*coordinates)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def _model_root(payload: bytes) -> ElementTree.Element:
    with ZipFile(io.BytesIO(payload)) as archive:
        self_names = set(archive.namelist())
        required = {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"}
        if not required <= self_names:
            raise AssertionError(f"missing 3MF parts: {required - self_names}")
        return ElementTree.fromstring(archive.read("3D/3dmodel.model"))


class _ReadOnlyStream:
    def write(self, payload: bytes) -> int:
        del payload
        raise PermissionError("read-only destination")


class ExportFormatsTest(unittest.TestCase):
    def test_stl_binary_ascii_stream_pathlike_and_units(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            binary_path = root / "inch-binary.stl"
            ascii_path = root / "mm-ascii.stl"
            shape = zencad.box(25.4)
            source = shape.native()
            before = encode_brep(source)

            zencad.export_stl(shape, binary_path, unit="in", binary=True)
            zencad.export_stl(shape, ascii_path, unit="mm", binary=False)

            binary = binary_path.read_bytes()
            self.assertEqual(len(binary), 84 + struct.unpack("<I", binary[80:84])[0] * 50)
            self.assertTrue(ascii_path.read_bytes().lstrip().startswith(b"solid"))
            self.assertAlmostEqual(_stl_bounds(binary_path)[1], 1.0)
            self.assertAlmostEqual(_stl_bounds(ascii_path)[1], 25.4)

            stream = io.BytesIO()
            zencad.export_stl(shape, stream, binary=True)
            self.assertGreater(len(stream.getvalue()), 84)
            self.assertTrue(zencad.to_stl(shape, root / "compat.stl", 0.1))
            self.assertEqual(encode_brep(source), before)

    def test_step_round_trip_stream_and_unit_metadata(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "shape.step"
            shape = zencad.box(25.4)
            zencad.export_step(shape, path, unit=typed.LengthUnit.INCH)

            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"ISO-10303-21"))
            self.assertIn(b"CONVERSION_BASED_UNIT('INCH'", payload)
            reader = STEPControl_Reader()
            self.assertEqual(reader.ReadFile(str(path)).name, "IFSelect_RetDone")
            self.assertGreater(reader.TransferRoots(), 0)
            restored = ResolvedShape(reader.OneShape())
            x_bounds = restored.bbox().xrange()
            self.assertAlmostEqual(x_bounds[1] - x_bounds[0], 25.4, places=6)

            stream = io.BytesIO()
            zencad.export_step(shape, stream)
            self.assertTrue(stream.getvalue().startswith(b"ISO-10303-21"))

    def test_3mf_archive_mesh_units_and_metadata(self):
        stream = io.BytesIO()
        zencad.export_3mf(
            zencad.box(25.4),
            stream,
            unit="inch",
            name="One inch cube",
            metadata={"Designer": "ZenCad"},
        )
        root = _model_root(stream.getvalue())
        namespace = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}

        self.assertEqual(root.attrib["unit"], "inch")
        object_node = root.find("m:resources/m:object", namespace)
        self.assertIsNotNone(object_node)
        assert object_node is not None
        self.assertEqual(object_node.attrib["type"], "model")
        self.assertEqual(object_node.attrib["name"], "One inch cube")
        vertices = root.findall("m:resources/m:object/m:mesh/m:vertices/m:vertex", namespace)
        triangles = root.findall(
            "m:resources/m:object/m:mesh/m:triangles/m:triangle", namespace
        )
        self.assertTrue(vertices)
        self.assertTrue(triangles)
        self.assertAlmostEqual(max(float(vertex.attrib["x"]) for vertex in vertices), 1)
        metadata = {
            node.attrib["name"]: node.text
            for node in root.findall("m:metadata", namespace)
        }
        self.assertEqual(metadata["Designer"], "ZenCad")

    def test_failures_name_format_and_invalid_shapes_are_rejected(self):
        shape = zencad.box(1)
        with self.assertRaisesRegex(OSError, "failed to write STL"):
            zencad.export_stl(shape, _ReadOnlyStream())
        with TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing" / "shape.3mf"
            with self.assertRaisesRegex(OSError, "failed to write 3MF"):
                zencad.export_3mf(shape, missing)
        with self.assertRaisesRegex(ValueError, "ASCII"):
            zencad.export_3mf(shape, io.BytesIO(), binary=False)
        with self.assertRaisesRegex(ValueError, "ASCII"):
            zencad.export_step(shape, io.BytesIO(), binary=True)
        context = typed.Context.deferred(cache=False)
        invalid = typed.Solid.from_ocp(_open_solid(), context=context)
        with self.assertRaises(ShapeValidationError):
            zencad.export_step(invalid, io.BytesIO())

    def test_typed_exports_work_in_every_evaluation_mode(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            with self.subTest(mode=mode):
                context = typed.Context(
                    mode=mode,
                    cache=True,
                    cache_store=MemoryCacheStore(),
                )
                shape = context.call(typed.box, 2)
                stl = io.BytesIO()
                step = io.BytesIO()
                three_mf = io.BytesIO()

                context.call(typed.export_stl, shape, stl)
                context.call(typed.export_step, shape, step)
                context.call(typed.export_3mf, shape, three_mf)

                self.assertGreater(len(stl.getvalue()), 84)
                self.assertTrue(step.getvalue().startswith(b"ISO-10303-21"))
                self.assertEqual(_model_root(three_mf.getvalue()).attrib["unit"], "millimeter")


if __name__ == "__main__":
    unittest.main()
