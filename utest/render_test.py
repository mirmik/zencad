import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from zencad.render import (
    contact_sheet_grid,
    parse_background,
    parse_size,
    parse_views,
    _camera_options,
    render_cli,
    render_script,
)


class RenderOptionsTest(unittest.TestCase):
    def test_camera_cardinal_directions_and_poles(self):
        cases = (
            (0, 0, (-1, 0, 0), (0, 0, 1)),
            (math.pi / 2, 0, (0, -1, 0), (0, 0, 1)),
            (0, math.pi / 2, (0, 0, -1), (-1, 0, 0)),
            (0, -math.pi / 2, (0, 0, 1), (1, 0, 0)),
        )
        for yaw, pitch, expected_direction, expected_up in cases:
            with self.subTest(yaw=yaw, pitch=pitch):
                labels, (direction, up) = _camera_options(None, yaw, pitch)
                self.assertEqual(labels, ("custom",))
                for actual, expected in zip(direction + up, expected_direction + expected_up):
                    self.assertAlmostEqual(actual, expected)
        _, (direction, up) = _camera_options(None, 1.2, 0.4)
        self.assertAlmostEqual(sum(a*b for a, b in zip(direction, up)), 0)
        self.assertAlmostEqual(sum(a*a for a in direction), 1)
        self.assertAlmostEqual(sum(a*a for a in up), 1)

    def test_invalid_camera_and_msaa_fail_before_script_evaluation(self):
        cases = (
            {"yaw": 0}, {"pitch": 0},
            {"yaw": 0, "pitch": 0, "views": ("front",)},
            {"yaw": float("nan"), "pitch": 0},
            {"yaw": 0, "pitch": float("inf")},
            {"yaw": 0, "pitch": math.pi},
            {"yaw": True, "pitch": 0},
            {"msaa": 3}, {"msaa": -1}, {"msaa": True}, {"msaa": 4.0},
        )
        with patch("zencad.render._evaluate_script") as evaluate:
            for options in cases:
                with self.subTest(options=options), self.assertRaises(ValueError):
                    render_script("unused.py", "unused.png", **options)
            evaluate.assert_not_called()

    def test_cli_converts_degrees_and_forwards_msaa(self):
        with patch("zencad.render.render_script", return_value=SimpleNamespace(path="out.png")) as render:
            self.assertEqual(render_cli([
                "model.py", "-o", "out.png", "--yaw", "-60", "--pitch", "15", "--msaa", "8",
            ]), 0)
        self.assertIsNone(render.call_args.kwargs["views"])
        self.assertAlmostEqual(render.call_args.kwargs["yaw"], -math.pi / 3)
        self.assertAlmostEqual(render.call_args.kwargs["pitch"], math.pi / 12)
        self.assertEqual(render.call_args.kwargs["msaa"], 8)

    def test_views_preserve_requested_order_and_accept_commas(self):
        self.assertEqual(
            parse_views(("iso,front", "top")),
            ("iso", "front", "top"),
        )
        with self.assertRaisesRegex(ValueError, "Unknown view"):
            parse_views("iso,portrait")
        with self.assertRaisesRegex(ValueError, "must not be repeated"):
            parse_views("front,front")

    def test_size_is_per_view_and_bounded(self):
        self.assertEqual(parse_size("640x480"), (640, 480))
        self.assertEqual(parse_size((320, 200)), (320, 200))
        for invalid in ("640", "0x480", "wide", (True, 200)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    parse_size(invalid)

    def test_background_uses_srgb_hex_components(self):
        self.assertEqual(parse_background("#102030"), (16 / 255, 32 / 255, 48 / 255))
        self.assertEqual(parse_background((0.1, 0.2, 0.3)), (0.1, 0.2, 0.3))
        with self.assertRaises(ValueError):
            parse_background("black")

    def test_contact_sheet_grid_is_near_square(self):
        self.assertEqual(contact_sheet_grid(1), (1, 1))
        self.assertEqual(contact_sheet_grid(4), (2, 2))
        self.assertEqual(contact_sheet_grid(7), (3, 3))
        with self.assertRaises(ValueError):
            contact_sheet_grid(0)


if __name__ == "__main__":
    unittest.main()
