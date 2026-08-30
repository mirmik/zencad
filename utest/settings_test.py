import builtins
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import unittest

from zencad.gui.navigation import DEFAULT_NAVIGATION_SCHEME
from zencad.settings import (
    DEFAULT_MSAA_SAMPLES,
    MSAA_SAMPLE_OPTIONS,
    ZencadSettings,
    default_settings_path,
    normalize_msaa_samples,
)


class SettingsTest(unittest.TestCase):
    def test_default_is_four_samples(self):
        settings = ZencadSettings()
        self.assertEqual(
            settings.get(["view", "msaa_samples"]),
            DEFAULT_MSAA_SAMPLES,
        )
        self.assertEqual(DEFAULT_MSAA_SAMPLES, 4)
        self.assertEqual(
            settings.get(["view", "navigation_scheme"]),
            DEFAULT_NAVIGATION_SCHEME,
        )
        self.assertEqual(settings.get(["view", "navigation_rotate"]), "left")
        self.assertEqual(settings.get(["view", "navigation_pan"]), "middle")
        self.assertEqual(settings.get(["view", "navigation_zoom"]), "none")
        self.assertFalse(
            settings.get(["view", "navigation_invert_wheel"])
        )
        self.assertFalse(
            settings.get(["view", "navigation_invert_orbit"])
        )

    def test_supported_values_are_preserved(self):
        for samples in MSAA_SAMPLE_OPTIONS:
            self.assertEqual(normalize_msaa_samples(samples), samples)
            self.assertEqual(normalize_msaa_samples(str(samples)), samples)

    def test_invalid_values_fall_back_to_default(self):
        for value in (None, "invalid", -1, 1, 3, 16):
            self.assertEqual(normalize_msaa_samples(value), DEFAULT_MSAA_SAMPLES)

    def test_linux_settings_path_matches_existing_qsettings_location(self):
        with mock.patch("zencad.settings.sys.platform", "linux"), mock.patch.dict(
            "os.environ",
            {"XDG_CONFIG_HOME": "/tmp/zencad-config-test"},
        ):
            self.assertEqual(
                default_settings_path(),
                Path("/tmp/zencad-config-test/ZenCad/settings.conf"),
            )

    def test_round_trip_does_not_import_pyqt(self):
        with TemporaryDirectory() as directory:
            class Rect:
                def x(self):
                    return 1

                def y(self):
                    return 2

                def width(self):
                    return 640

                def height(self):
                    return 480

            path = Path(directory) / "ZenCad" / "settings.conf"
            settings = ZencadSettings(path)
            settings.set(["view", "default_color"], (0.1, 0.2, 0.3, 0.4))
            settings.set(["memory", "wsize"], Rect())
            settings.set(["memory", "recents"], ["one.py", "two.py"])

            original_import = builtins.__import__

            def guarded_import(name, *args, **kwargs):
                if name == "PyQt5" or name.startswith("PyQt5."):
                    raise AssertionError("settings imported PyQt5")
                return original_import(name, *args, **kwargs)

            with mock.patch("builtins.__import__", side_effect=guarded_import):
                settings.store()
                restored = ZencadSettings(path)
                restored.restore()

            self.assertEqual(
                restored.get(["view", "default_color"]),
                [0.1, 0.2, 0.3, 0.4],
            )
            self.assertEqual(
                restored.get(["memory", "wsize"]),
                [1, 2, 640, 480],
            )
            self.assertEqual(
                restored.get(["memory", "recents"]),
                ["one.py", "two.py"],
            )

    def test_reads_legacy_qsettings_ini_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.conf"
            path.write_text(
                """\
[gui]
text_editor=custom-editor {path}
unknown_legacy_key=preserved

[memory]
console_hidden=true
hsplitter_position=959, 1597
recents=/tmp/one.py, /tmp/two.py
wsize=@Rect(10 20 800 600)

[view]
msaa_samples=8
""",
                encoding="utf-8",
            )
            settings = ZencadSettings(path)
            settings.restore()

            self.assertEqual(
                settings.get(["gui", "text_editor"]),
                "custom-editor {path}",
            )
            self.assertTrue(settings.get(["memory", "console_hidden"]))
            self.assertEqual(
                settings.get(["memory", "hsplitter_position"]),
                [959, 1597],
            )
            self.assertEqual(
                settings.get(["memory", "wsize"]),
                [10, 20, 800, 600],
            )
            self.assertEqual(settings.get(["view", "msaa_samples"]), 8)

            settings.store()
            self.assertIn(
                "unknown_legacy_key = preserved",
                path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
