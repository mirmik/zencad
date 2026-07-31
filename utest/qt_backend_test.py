import importlib.util
from pathlib import Path
import unittest


def load_qt_backend():
    path = Path(__file__).parents[1] / "zencad" / "gui" / "qt_backend.py"
    spec = importlib.util.spec_from_file_location("zencad_qt_backend", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QtBackendSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = load_qt_backend()

    def test_wayland_uses_xcb_when_xwayland_is_available(self):
        environment = {
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":1",
        }

        selected = self.backend.configure_qt_platform(
            environment, platform="linux"
        )

        self.assertEqual(selected, "xcb")
        self.assertEqual(environment["QT_QPA_PLATFORM"], "xcb")

    def test_explicit_qt_backend_is_preserved(self):
        environment = {
            "XDG_SESSION_TYPE": "wayland",
            "DISPLAY": ":1",
            "QT_QPA_PLATFORM": "wayland",
        }

        selected = self.backend.configure_qt_platform(
            environment, platform="linux"
        )

        self.assertEqual(selected, "wayland")
        self.assertEqual(environment["QT_QPA_PLATFORM"], "wayland")

    def test_non_wayland_session_is_unchanged(self):
        environment = {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"}

        selected = self.backend.configure_qt_platform(
            environment, platform="linux"
        )

        self.assertIsNone(selected)
        self.assertNotIn("QT_QPA_PLATFORM", environment)


if __name__ == "__main__":
    unittest.main()
