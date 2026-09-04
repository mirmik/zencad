import math
import unittest

import zencad
import zencad.assemble as assemble


class AssemblyKinematics(unittest.TestCase):
    def assertPointAlmostEqual(self, point, expected):
        for actual, wanted in zip(point, expected):
            self.assertAlmostEqual(actual, wanted, places=8)

    def test_unit_tree_local_and_global_locations(self):
        root = assemble.unit(location=zencad.translate(1, 0, 0))
        child = assemble.unit(
            parent=root, location=zencad.translate(0, 2, 0)
        )
        leaf = assemble.unit(
            parent=child, location=zencad.translate(0, 0, 3)
        )

        root.location_update(deep=True, view=False)

        self.assertIn(child, root.childs)
        self.assertIn(leaf, root.deep_childs_list())
        self.assertPointAlmostEqual(
            leaf.global_location.translation(), (1, 2, 3)
        )

    def test_rotator_updates_linked_subtree(self):
        root = assemble.unit(location=zencad.translate(10, 0, 0))
        joint = assemble.rotator(
            axis=(0, 0, 1),
            parent=root,
            location=zencad.translate(0, 5, 0),
        )
        payload = assemble.unit(location=zencad.translate(2, 0, 0))
        joint.link(payload)
        root.location_update(deep=True, view=False)

        joint.set_coord(math.pi / 2, view=False)

        self.assertAlmostEqual(joint.coord, math.pi / 2)
        self.assertPointAlmostEqual(
            payload.global_location.translation(), (10, 7, 0)
        )

    def test_actuator_updates_linked_subtree(self):
        joint = assemble.actuator(axis=(1, 0, 0), mul=2)
        payload = assemble.unit(location=zencad.translate(0, 3, 0))
        joint.link(payload)
        joint.location_update(deep=True, view=False)

        joint.set_coord(4, view=False)

        self.assertEqual(joint.coord, 4)
        self.assertPointAlmostEqual(
            payload.global_location.translation(), (8, 3, 0)
        )


if __name__ == "__main__":
    unittest.main()
