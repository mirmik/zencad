import unittest
import zencad
import math
import pickle


def early(a, b):
    if abs(a.x - b.x) > 0.0001:
        return False
    if abs(a.y - b.y) > 0.0001:
        return False
    if abs(a.z - b.z) > 0.0001:
        return False
    return True


class TransformationProbe(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def assertPointAlmostEqual(self, actual, expected):
        self.assertAlmostEqual(actual.x, expected.x, places=12)
        self.assertAlmostEqual(actual.y, expected.y, places=12)
        self.assertAlmostEqual(actual.z, expected.z, places=12)

    def test_translate(self):
        x = 10
        y = 20
        z = 30
        v = 10

        pnt = zencad.point3(x, y, z)

        self.assertEqual(zencad.translate(z, y, x)(pnt),
                         zencad.point3(40, 40, 40))

        self.assertEqual(zencad.up(v)(pnt), zencad.point3(x, y, z+v))
        self.assertEqual(zencad.down(v)(pnt), zencad.point3(x, y, z-v))
        self.assertEqual(zencad.left(v)(pnt), zencad.point3(x-v, y, z))
        self.assertEqual(zencad.right(v)(pnt), zencad.point3(x+v, y, z))
        self.assertEqual(zencad.forw(v)(pnt), zencad.point3(x, y+v, z))
        self.assertEqual(zencad.back(v)(pnt), zencad.point3(x, y-v, z))

        self.assertEqual(zencad.moveX(v)(pnt), zencad.point3(x+v, y, z))
        self.assertEqual(zencad.moveY(v)(pnt), zencad.point3(x, y+v, z))
        self.assertEqual(zencad.moveZ(v)(pnt), zencad.point3(x, y, z+v))

    def test_rotate(self):
        x = 10
        y = 20
        z = 30
        v = 10

        pnt = zencad.point3(x, y, z)

        ang = zencad.deg(v)
        self.assertPointAlmostEqual(
            zencad.rotateX(ang)(pnt),
            zencad.point3(
                x,
                y*math.cos(ang)-z*math.sin(ang),
                z*math.cos(ang)+y*math.sin(ang))
        )

        self.assertPointAlmostEqual(
            zencad.rotateY(ang)(pnt),
            zencad.point3(
                x*math.cos(ang)+z*math.sin(ang),
                y,
                z*math.cos(ang)-x*math.sin(ang))
        )

        self.assertPointAlmostEqual(
            zencad.rotateZ(ang)(pnt),
            zencad.point3(
                x*math.cos(ang)-y*math.sin(ang),
                y*math.cos(ang)+x*math.sin(ang),
                z)
        )

    def test_trans_shape(self):
        x = 10
        y = 20
        z = 30

        box = zencad.box(10, 10, 10, center=True).translate(x, y, z)

        self.assertEqual(
            box.transform(zencad.translate(z, y, x)).center().value(),
            (40.0, 40.0, 40.0),
        )

    def test_short_rotate(self):
        t = zencad.short_rotate((0, 0, 1), (1, 0, 0))

        m = zencad.point3(0, 0, 1)
        m = t(m)

        self.assertEqual(
            tuple(round(component, 4) for component in m.value()),
            (1.0, 0.0, 0.0),
        )

    def test_pickle_restores_similarity_transform_state(self):
        transform = (
            zencad.move(1, 2, 3)
            * zencad.rotateZ(math.pi / 4)
            * zencad.scale(-2)
        )
        restored = pickle.loads(pickle.dumps(transform))
        with zencad.using_context(restored.context):
            restored_point = zencad.point3(3, -2, 5)
            restored_value = restored.transform_point(restored_point).value()
        with zencad.using_context(transform.context):
            original_point = zencad.point3(3, -2, 5)
            original_value = transform.transform_point(original_point).value()
        self.assertEqual(restored_value, original_value)
        self.assertEqual(restored.translation.value(), transform.translation.value())
