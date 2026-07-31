import importlib.util
from pathlib import Path
import io
from tempfile import TemporaryDirectory
import unittest
from unittest import mock


try:
    import OCP  # noqa: F401
except ImportError:
    OCP_AVAILABLE = False
else:
    OCP_AVAILABLE = True


def load_occ_compat():
    path = Path(__file__).parents[1] / "zencad" / "occ_compat.py"
    spec = importlib.util.spec_from_file_location("zencad_occ_compat", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OCPCompatibilityDiagnostics(unittest.TestCase):
    def test_missing_ocp_has_actionable_error(self):
        real_import = __import__

        def import_without_ocp(name, *args, **kwargs):
            if name == "OCP" or name.startswith("OCP."):
                raise ImportError("OCP hidden by test")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=import_without_ocp):
            with self.assertRaisesRegex(ImportError, "cadquery-ocp-novtk"):
                load_occ_compat()


@unittest.skipUnless(OCP_AVAILABLE, "cadquery-ocp is not installed")
class OCPCompatibilityBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compat = load_occ_compat()

    def test_version_precision_downcast_and_properties(self):
        from OCP.Bnd import Bnd_Box
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCP.GProp import GProp_GProps

        shape = BRepPrimAPI_MakeBox(2.0, 3.0, 4.0).Shape()
        properties = GProp_GProps()
        self.compat.volume_properties(shape, properties)

        self.assertEqual(self.compat.BACKEND_NAME, "OCP")
        self.assertTrue(self.compat.BACKEND_VERSION)
        self.assertGreater(self.compat.confusion(), 0.0)
        self.assertAlmostEqual(properties.Mass(), 24.0, places=8)
        self.assertFalse(self.compat.as_solid(shape).IsNull())
        self.assertAlmostEqual(self.compat.direction_z().Z(), 1.0)

        bounds = Bnd_Box()
        self.compat.add_to_bounds(shape, bounds)
        self.assertFalse(bounds.IsVoid())
        self.assertIsNotNone(self.compat.make_sewing())

    def test_brep_round_trip_and_typed_exception(self):
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCP.TopoDS import TopoDS_Shape

        shape = BRepPrimAPI_MakeBox(2.0, 3.0, 4.0).Shape()
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "shape.brep"
            self.assertTrue(self.compat.write_brep(shape, path))

            loaded = TopoDS_Shape()
            self.assertTrue(self.compat.read_brep(loaded, path))
            self.assertFalse(loaded.IsNull())

            stream = io.BytesIO()
            self.compat.write_brep(shape, stream)
            loaded_from_stream = TopoDS_Shape()
            self.compat.read_brep(
                loaded_from_stream, io.BytesIO(stream.getvalue())
            )
            self.assertFalse(loaded_from_stream.IsNull())

        # OCCT may expose this validation failure as the more specific
        # Standard_DomainError or as its Standard_Failure base class,
        # depending on the platform build.
        with self.assertRaises(self.compat.Standard_Failure):
            BRepPrimAPI_MakeBox(0.0, 2.0, 3.0).Shape()


if __name__ == "__main__":
    unittest.main()
