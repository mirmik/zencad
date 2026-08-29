import unittest

from zencad.gui.navigation import DEFAULT_NAVIGATION_SCHEME
from zencad.settings import (
    DEFAULT_MSAA_SAMPLES,
    MSAA_SAMPLE_OPTIONS,
    ZencadSettings,
    normalize_msaa_samples,
)


class MsaaSettingsTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
