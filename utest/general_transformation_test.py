import unittest
import zencad
import pickle


def early(a, b):
    left = a.point().value()
    right = b.point().value()
    return all(abs(x - y) <= 0.0001 for x, y in zip(left, right))


def vertex_set_issame(a, b):
    for x in a:
        for y in b:
            if early(x, y):
                break
        else:
            return False

    for x in b:
        for y in a:
            if early(x, y):
                break
        else:
            return False

    return True


class GeneralTransformation(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_scale(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(20, 30, 40)
        scale = zencad.scaleXYZ(2, 3, 4)

        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleX(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(20, 10, 10)
        scale = zencad.scaleX(2)

        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleY(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(10, 30, 10)
        scale = zencad.scaleY(3)

        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleZ(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(10, 10, 40)
        scale = zencad.scaleZ(4)

        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_composition_application_and_pickle(self):
        first = zencad.scaleXYZ(2, 3, 4)
        second = zencad.scaleXYZ(5, 7, 11)
        composed = first * second
        source = zencad.box(1, 1, 1)
        expected = zencad.box(10, 21, 44)

        self.assertTrue(
            vertex_set_issame(source.transform(composed).vertices(), expected.vertices())
        )

        restored = pickle.loads(pickle.dumps(composed))
        restored_source = restored.context.call(zencad.box, 1, 1, 1)
        restored_shape = restored_source.transform(restored)
        self.assertTrue(
            vertex_set_issame(
                restored_shape.vertices(),
                expected.vertices(),
            )
        )
