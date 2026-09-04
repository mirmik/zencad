import unittest

from zencad.gui.navigation import (
    DEFAULT_NAVIGATION_SCHEME,
    custom_bindings_conflict,
    navigation_drag_action,
    normalize_navigation_scheme,
    wheel_zoom_factor,
)


class NavigationTest(unittest.TestCase):
    def test_default_uses_middle_and_right_drag_for_pan(self):
        self.assertEqual(
            navigation_drag_action("zencad", ["left"], []),
            "rotate",
        )
        self.assertEqual(
            navigation_drag_action("zencad", ["middle"], []),
            "pan",
        )
        self.assertEqual(
            navigation_drag_action("zencad", ["right"], []),
            "pan",
        )

    def test_classic_preserves_middle_drag_zoom(self):
        self.assertEqual(
            navigation_drag_action("classic", ["middle"], []),
            "zoom",
        )

    def test_blender_uses_middle_drag_modifiers(self):
        self.assertEqual(
            navigation_drag_action("blender", ["middle"], []),
            "rotate",
        )
        self.assertEqual(
            navigation_drag_action("blender", ["middle"], ["shift"]),
            "pan",
        )
        self.assertEqual(
            navigation_drag_action("blender", ["middle"], ["control"]),
            "zoom",
        )

    def test_freecad_uses_middle_pan_and_button_chord_for_rotation(self):
        self.assertEqual(
            navigation_drag_action("freecad", ["middle"], []),
            "pan",
        )
        self.assertEqual(
            navigation_drag_action(
                "freecad", ["left", "middle"], []
            ),
            "rotate",
        )

    def test_maya_requires_alt_mouse_gestures(self):
        self.assertEqual(
            navigation_drag_action("maya", ["left"], ["alt"]),
            "rotate",
        )
        self.assertEqual(
            navigation_drag_action("maya", ["middle"], ["alt"]),
            "pan",
        )
        self.assertEqual(
            navigation_drag_action("maya", ["right"], ["alt"]),
            "zoom",
        )

    def test_custom_bindings_and_conflicts(self):
        bindings = {
            "rotate": "alt+left",
            "pan": "shift+middle",
            "zoom": "control+right",
        }
        self.assertEqual(
            navigation_drag_action(
                "custom", ["middle"], ["shift"], bindings
            ),
            "pan",
        )
        self.assertFalse(custom_bindings_conflict(bindings))
        bindings["zoom"] = "shift+middle"
        self.assertTrue(custom_bindings_conflict(bindings))

    def test_wheel_zoom_can_be_inverted(self):
        self.assertGreater(wheel_zoom_factor(120), 1)
        self.assertLess(wheel_zoom_factor(-120), 1)
        self.assertLess(wheel_zoom_factor(120, inverted=True), 1)
        self.assertGreater(wheel_zoom_factor(-120, inverted=True), 1)

    def test_unknown_scheme_falls_back_to_default(self):
        self.assertEqual(
            normalize_navigation_scheme("unknown"),
            DEFAULT_NAVIGATION_SCHEME,
        )


if __name__ == "__main__":
    unittest.main()
