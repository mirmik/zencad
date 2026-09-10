import unittest

import numpy as np

from zencad import translate, rotate, rotateX, rotateY, rotateZ, mirrorYZ, scale
from zencad.assemble import unit, rotator, actuator, planemover
from zencad.libs.kinematic import kinematic_chain


def matrix(transform):
    return np.array([[transform._trsf.Value(i, j) for j in range(1, 5)]
                     for i in range(1, 4)])


def numerical_jacobian(joints, target, basis, eps=1e-6):
    """Differentiate placement independently; freeze the reporting frame.

    dA A^-1 also handles mirrored/scaled placements. Conjugating this spin
    matrix changes its axes without scaling the angular velocity.
    """
    original = matrix(target())
    inverse_a = np.linalg.inv(original[:, :3])
    b = matrix(basis)[:, :3]
    inverse_b = np.linalg.inv(b)
    columns = []
    for joint in joints:
        q = joint.coord
        try:
            joint.set_coord(q + eps, view=False)
            plus = matrix(target())
            joint.set_coord(q - eps, view=False)
            minus = matrix(target())
        finally:
            joint.set_coord(q, view=False)
        derivative = (plus - minus) / (2 * eps)
        spin = inverse_b @ derivative[:, :3] @ inverse_a @ b
        angular = np.array([spin[2, 1] - spin[1, 2],
                            spin[0, 2] - spin[2, 0],
                            spin[1, 0] - spin[0, 1]]) / 2
        columns.append(np.r_[angular, inverse_b @ derivative[:, 3]])
    return np.array(columns).T if columns else np.zeros((6, 0))


class KinematicTest(unittest.TestCase):
    def assert_jacobian(self, chain, body, local, basis):
        target = lambda: body.global_location * local
        expected = numerical_jacobian(chain.kinematic_pairs, target,
                                      target() if basis is None else basis.global_location)
        actual = chain.sensitivity_jacobian2(body, local, basis)
        np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=1e-7)
        np.testing.assert_allclose(chain.translation_sensitivity_jacobian2(body, local, basis),
                                   expected[3:], atol=1e-7, rtol=1e-7)

    def test_random_chains_and_bases(self):
        for seed in range(30):
            rng = np.random.default_rng(seed)
            placement = lambda: translate(*rng.normal(size=3)) * rotate(
                rng.normal(size=3), float(rng.normal()))
            root = unit(location=placement())
            parent = root
            joints = []
            for cls, mul in zip((rotator, actuator, rotator, actuator), (-2, .7, 1.3, -.4)):
                joint = cls(axis=rng.normal(size=3), mul=mul, parent=parent, location=placement())
                joint.set_coord(float(rng.normal()), view=False)
                joints.append(joint)
                parent = unit(parent=joint.output, location=placement())
            root.location_update(deep=True, view=False)
            chain = kinematic_chain(parent, root)
            identity = unit().location
            for basis in (None, root, joints[1].output):
                with self.subTest(seed=seed, basis=basis):
                    self.assert_jacobian(chain, parent, identity, basis)
                    np.testing.assert_allclose(chain.sensivity_jacobian(basis),
                                               chain.sensitivity_jacobian2(parent, identity, basis))
                    np.testing.assert_allclose(chain.translation_sensivity_jacobian(basis),
                                               chain.sensivity_jacobian(basis)[3:])
            self.assert_jacobian(chain, joints[1].output,
                                 unit(location=translate(.4, -.7, 1.1) * rotateX(.5)).location, root)

    def test_inputs_branches_and_fixed_targets(self):
        root = unit()
        common = rotator(axis=(0, 0, 1), parent=root)
        left = actuator(axis=(1, 0, 0), parent=common.output, location=translate(1, 2, 0))
        right = rotator(axis=(0, 1, 0), parent=common.output, location=translate(2, 1, 0))
        tip = unit(parent=left.output)
        sibling = unit(parent=right.output, location=translate(3, 1, 0))
        # Attached to the input: even its kinematic parent does not move it.
        input_child = unit(parent=left, location=translate(4, 0, 0))
        identity = unit().location
        root.location_update(deep=True, view=False)
        for end, start in ((tip, root), (left, root), (tip, left), (tip, common.output)):
            chain = kinematic_chain(end, start)
            for target in (end, sibling, left, input_child, root, unit()):
                self.assert_jacobian(chain, target, identity, root)
            np.testing.assert_allclose(chain.sensivity_jacobian(root),
                                       numerical_jacobian(chain.kinematic_pairs,
                                                          lambda: end.global_location, root.global_location),
                                       atol=1e-7)

    def test_mirrors_and_scale_in_all_frames(self):
        for placement in (mirrorYZ(), scale(2), scale(-.5),
                          rotateX(.4) * mirrorYZ() * scale(3)):
            world = unit()
            mount = unit(parent=world, location=placement)
            joint = rotator(axis=(1, 2, 3), mul=-1.7, parent=mount)
            slide = actuator(axis=(2, -1, 3), parent=joint.output, location=rotateY(.3))
            tip = unit(parent=slide.output, location=translate(3, 1, -2) * mirrorYZ() * scale(.7))
            joint.set_coord(.3, view=False)
            slide.set_coord(.4, view=False)
            chain = kinematic_chain(tip, world)
            for basis in (None, world, mount, joint.output):
                self.assert_jacobian(chain, tip, unit().location, basis)

    def test_fixed_block_order_and_empty_chain(self):
        root = unit(location=rotateZ(.7))
        tip = unit(parent=root, location=translate(3, 0, 0))
        root.location_update(deep=True, view=False)
        chain = kinematic_chain(tip)
        np.testing.assert_allclose(matrix(chain.simplified_chain[0]), matrix(tip.global_location))
        self.assertEqual(chain.sensivity_jacobian().shape, (6, 0))
        chain.apply_step([])

    def test_invalid_proximal(self):
        with self.assertRaisesRegex(ValueError, 'ancestor'):
            kinematic_chain(unit(), unit())

    def test_apply_validation_before_mutation(self):
        root = rotator(axis=(0, 0, 1))
        child = actuator(axis=(1, 0, 0), parent=root.output)
        chain = kinematic_chain(child.output)
        for changes in ([1], [1, 2, 3]):
            with self.assertRaises(ValueError):
                chain.apply_step(changes)
            self.assertEqual((root.coord, child.coord), (0, 0))
        chain.apply([2, 3], .5)
        self.assertEqual((root.coord, child.coord), (1.5, 1))
        planar = planemover(parent=child.output)
        with self.assertRaises(NotImplementedError):
            kinematic_chain(planar.output).apply_step([1, 2, 3])
        self.assertEqual((root.coord, child.coord), (1.5, 1))

    def test_planemover_translation_and_descendants(self):
        planar = planemover()
        tip = unit(parent=planar.output, location=translate(3, 0, 0))
        planar.set_coords([2, 4], view=False)
        np.testing.assert_allclose(matrix(tip.global_location)[:, 3], [5, 4, 0])
        # Keep the existing distal-first ordering inside multi-DOF pairs.
        expected = np.zeros((6, 2))
        expected[4, 0] = expected[3, 1] = 1
        np.testing.assert_allclose(kinematic_chain(tip).sensivity_jacobian(), expected)


if __name__ == '__main__':
    unittest.main()
