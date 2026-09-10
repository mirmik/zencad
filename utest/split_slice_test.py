import unittest

import zencad
from zencad import geom as typed


class SplitSliceTest(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_split_orders_multiple_parts_and_preserves_graph_nodes(self):
        body = zencad.box(10)
        tools = (zencad.infplane().up(3), zencad.infplane().up(7))

        parts = zencad.split(body, tools)
        repeated = zencad.split(body, tools)

        self.assertIsInstance(parts, zencad.SplitResult)
        self.assertEqual(len(parts), 3)
        self.assertTrue(all(isinstance(part, zencad.Shape) for part in parts))
        self.assertEqual(parts[0]._state.digest, repeated[0]._state.digest)
        self.assertEqual(
            [round(float(part.mass()), 5) for part in parts], [300, 400, 300]
        )
        self.assertEqual(
            [round(float(part.center().z), 5) for part in parts],
            [1.5, 5.0, 8.5],
        )

    def test_split_accepts_disjoint_and_touching_tools(self):
        for mode in (typed.Context.immediate, typed.Context.deferred):
            with self.subTest(mode=mode), typed.using_context(mode(cache=False)):
                body = zencad.box(2)
                tools = (
                    zencad.infplane().up(3),
                    zencad.infplane().up(2),
                    zencad.infplane(),
                    zencad.box(2).right(5),
                    zencad.box(2).right(2),
                )
                for index, tool in enumerate(tools):
                    with self.subTest(tool=index):
                        parts = zencad.split(body, tool)
                        self.assertEqual(len(parts), 1)
                        self.assertIsInstance(parts[0], zencad.Solid)
                        parts[0].assert_valid()
                        self.assertAlmostEqual(float(parts[0].mass()), 8)
                        self.assertAlmostEqual(float((body - parts[0]).mass()), 0)
                        self.assertAlmostEqual(float((parts[0] - body).mass()), 0)

                # No-op tools may also accompany an actual cut.
                parts = zencad.split(body, (tools[0], zencad.infplane().up(1)))
                self.assertEqual([round(float(p.mass()), 6) for p in parts], [4, 4])
                with self.assertRaisesRegex(ValueError, "at least one"):
                    len(zencad.split(body, ()))

                # Preserve all original solids when the input contains several.
                compound = body + body.right(4)
                parts = zencad.split(compound, tools[0])
                self.assertEqual([round(float(p.mass()), 6) for p in parts], [8, 8])
                self.assertEqual([round(float(p.center().x), 6) for p in parts], [1, 5])

    def test_slice_accepts_disjoint_and_touching_planes(self):
        for mode in (typed.Context.immediate, typed.Context.deferred):
            with self.subTest(mode=mode), typed.using_context(mode(cache=False)):
                body = zencad.box(2)
                for axis in ("x", "y", "z"):
                    for coordinate in (-1, 0, 2, 3):
                        with self.subTest(axis=axis, coordinate=coordinate):
                            parts = zencad.slice(body, z=coordinate, axis=axis)
                            self.assertEqual(len(parts), 1)
                            (part,) = parts
                            self.assertIsInstance(part, zencad.Solid)
                            part.assert_valid()
                            self.assertAlmostEqual(float(part.mass()), 8)
                            self.assertAlmostEqual(float((body - part).mass()), 0)
                            self.assertAlmostEqual(float((part - body).mass()), 0)
                            self.assertEqual(len(parts[:]), 1)
                            self.assertAlmostEqual(float(parts.lower.mass()), 8)
                            with self.assertRaises(IndexError):
                                parts.upper.native()

                for plane in (zencad.infplane().up(3), ((0, 0, 3), (0, 0, -1))):
                    parts = zencad.slice(body, plane=plane)
                    self.assertEqual(len(parts), 1)
                    self.assertAlmostEqual(float(parts[0].mass()), 8)

    def test_slice_preserves_all_parts_and_orders_by_plane_normal(self):
        for mode in (typed.Context.immediate, typed.Context.deferred):
            with self.subTest(mode=mode), typed.using_context(mode(cache=False)):
                body = zencad.box(2) + zencad.box(2).right(4)
                for height in (2, 3):
                    parts = zencad.slice(body, z=height)
                    self.assertEqual([round(float(p.mass()), 6) for p in parts], [8, 8])
                for normal in ((0, 0, 1), (0, 0, -1)):
                    parts = zencad.slice(body, plane=((0, 0, 1), normal))
                    self.assertEqual(len(parts), 4)
                    self.assertEqual([round(float(p.mass()), 6) for p in parts], [4]*4)
                    heights = [round(float(p.center().z), 6) for p in parts]
                    self.assertEqual(heights, sorted(heights, reverse=normal[2] < 0))
                    for part in parts:
                        part.assert_valid()

    def test_native_split_and_slice_accept_variable_part_counts(self):
        from zencad._native import boolops

        body = zencad.box(2)._legacy()
        for height in (-1, 0, 2, 3):
            for parts in (
                boolops.split(body, zencad.infplane().up(height)._legacy()),
                boolops.slice(body, z=height),
            ):
                self.assertEqual(len(parts), 1)
                self.assertAlmostEqual(parts[0].mass(), 8)
        sliced = boolops.slice(body, z=3)
        self.assertAlmostEqual(sliced.lower.mass(), 8)
        with self.assertRaises(IndexError):
            sliced.upper
        compound = (zencad.box(2) + zencad.box(2).right(4))._legacy()
        self.assertEqual(len(boolops.slice(compound, z=3)), 2)
        parts = boolops.slice(compound, z=1)
        self.assertEqual(len(parts), 4)
        self.assertEqual([round(p.mass(), 6) for p in parts], [4]*4)
        self.assertEqual([round(p.center().z, 6) for p in parts], [0.5, 0.5, 1.5, 1.5])
        lower, upper = boolops.slice(body, z=1)
        self.assertAlmostEqual(lower.mass(), 4)
        self.assertAlmostEqual(upper.mass(), 4)

    def test_slice_supports_coordinate_axis_and_arbitrary_plane(self):
        lower, upper = zencad.slice(zencad.box(10), z=4)
        self.assertIsInstance(lower, zencad.Shape)
        self.assertEqual(
            [round(float(lower.mass()), 5), round(float(upper.mass()), 5)], [400, 600]
        )
        self.assertLess(lower.center().z, upper.center().z)

        left, right = zencad.slice(zencad.box(10), z=2, axis="x")
        self.assertEqual(
            [round(float(left.mass()), 5), round(float(right.mass()), 5)],
            [200, 800],
        )
        self.assertLess(left.center().x, right.center().x)

        negative, positive = zencad.slice(
            zencad.box(10),
            plane=((0, 5, 0), (0, 1, 0)),
        )
        self.assertEqual(
            [round(float(negative.mass()), 5), round(float(positive.mass()), 5)],
            [500, 500],
        )
        self.assertLess(negative.center().y, positive.center().y)

    def test_typed_split_and_slice_share_the_resolved_backend(self):
        context = typed.Context.deferred(cache=False)
        with typed.using_context(context):
            body = typed.box(10)
            plane = typed.infplane().translate(typed.vector3(0, 0, 5))
            parts = typed.split(body, plane)
            sliced = typed.slice(body, z=4)

        self.assertIsInstance(parts, typed.SplitResult)
        self.assertEqual(len(parts), 2)
        self.assertTrue(all(part.context is context for part in parts))
        self.assertEqual([round(float(part.mass()), 5) for part in parts], [500, 500])
        self.assertIsInstance(sliced, typed.SliceResult)
        self.assertIs(sliced.lower.context, context)
        self.assertEqual(
            [
                round(float(sliced.lower.mass()), 5),
                round(float(sliced.upper.mass()), 5),
            ],
            [400, 600],
        )


if __name__ == "__main__":
    unittest.main()
