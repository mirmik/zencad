import unittest

import zencad
from zencad import _typed as typed


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
        self.assertEqual([round(float(part.mass()), 5) for part in parts], [300, 400, 300])
        self.assertEqual(
            [round(float(part.center().z), 5) for part in parts],
            [1.5, 5.0, 8.5],
        )

    def test_split_rejects_empty_and_non_dividing_tools(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            zencad.split(zencad.box(2), ())
        with self.assertRaisesRegex(ValueError, "do not divide"):
            len(zencad.split(zencad.box(2), zencad.infplane().up(3)))
        with self.assertRaisesRegex(ValueError, "do not divide"):
            len(zencad.split(zencad.box(2), zencad.infplane().up(2)))

    def test_slice_supports_coordinate_axis_and_arbitrary_plane(self):
        lower, upper = zencad.slice(zencad.box(10), z=4)
        self.assertIsInstance(lower, zencad.Shape)
        self.assertEqual([round(float(lower.mass()), 5), round(float(upper.mass()), 5)], [400, 600])
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
            [round(float(sliced.lower.mass()), 5), round(float(sliced.upper.mass()), 5)],
            [400, 600],
        )


if __name__ == "__main__":
    unittest.main()
