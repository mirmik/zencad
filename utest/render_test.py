import unittest

from zencad.render import (
    contact_sheet_grid,
    parse_background,
    parse_size,
    parse_views,
)


class RenderOptionsTest(unittest.TestCase):
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
