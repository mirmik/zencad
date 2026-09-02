import math
import unittest

import zencad
from zencad import geom as typed
from zencad.operation import using_context


class TypedRotateArrayCompatibilityTest(unittest.TestCase):
    def assertCoordinatesAlmostEqual(self, actual, expected):
        for left, right in zip(actual, expected):
            self.assertAlmostEqual(left, right, places=10)

    def test_rotate_array_interpolates_endpoint_semantics(self):
        context = typed.Context.deferred(cache=False)
        with using_context(context):
            point = typed.point3(1, 0, 0)
            open_array = typed.rotate_array(
                4,
                yaw=math.pi,
                endpoint=False,
                array=True,
            )
            closed_array = typed.rotate_array(
                4,
                yaw=math.pi,
                endpoint=True,
                array=True,
            )

        self.assertIs(zencad.rotate_array, typed.rotate_array)
        self.assertEqual(len(open_array), 4)
        self.assertCoordinatesAlmostEqual(
            open_array.transforms[-1](point).value(),
            (-math.sqrt(0.5), math.sqrt(0.5), 0),
        )
        self.assertCoordinatesAlmostEqual(
            closed_array.transforms[-1](point).value(),
            (-1, 0, 0),
        )

    def test_rotate_array2_preserves_radial_positions_and_roll(self):
        context = typed.Context.deferred(cache=False)
        with using_context(context):
            transforms = typed.rotate_array2(
                3,
                r=10,
                yaw=(0, math.pi),
                roll=(0, math.pi / 2),
                endpoint=True,
                array=True,
            )
            origin = typed.point3()
            direction = typed.vector3(1, 0, 0)

        positions = tuple(transform(origin).value() for transform in transforms)
        self.assertCoordinatesAlmostEqual(positions[0], (10, 0, 0))
        self.assertCoordinatesAlmostEqual(positions[1], (0, 10, 0))
        self.assertCoordinatesAlmostEqual(positions[2], (-10, 0, 0))
        self.assertCoordinatesAlmostEqual(
            transforms.transforms[0](direction).value(),
            (1, 0, 0),
        )
        self.assertCoordinatesAlmostEqual(
            transforms.transforms[-1](direction).value(),
            (0, 0, 1),
        )

    def test_rotate_arrays_apply_as_fused_or_array_multitransforms(self):
        context = typed.Context.deferred(cache=False)
        with using_context(context):
            shape = typed.box(1).right(3)
            fused = typed.rotate_array(3)(shape)
            items = typed.rotate_array2(3, r=3, array=True)(shape)

        self.assertIsInstance(fused, typed.Shape)
        self.assertEqual(len(items), 3)
        self.assertTrue(all(type(item) is typed.Solid for item in items))
        self.assertFalse(fused.native().IsNull())
        self.assertTrue(all(not item.native().IsNull() for item in items))


if __name__ == "__main__":
    unittest.main()
