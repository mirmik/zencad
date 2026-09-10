import unittest

import zencad as z
from evalcache import EvaluationMode
from zencad.assemble import unit


class MultiTransformTest(unittest.TestCase):
    def test_factories_preserve_geometry_and_context(self):
        for mode in EvaluationMode:
            with self.subTest(mode=mode), z.using_context(z.Context(mode=mode, cache=False)):
                body = z.box(2)
                transforms = [z.transform(), z.right(body.mass())]
                for factory in (z.multitrans, z.multitransform):
                    copies = factory(transforms, array=True)(body)
                    self.assertEqual(len(copies), 2)
                    self.assertTrue(all(type(s) is z.Solid for s in copies))
                    self.assertTrue(all(s.context is body.context for s in copies))
                    self.assertAlmostEqual(float(copies[1].center().x), 9)
                    self.assertAlmostEqual(float(factory(transforms)(body).mass()), 16)
                for factory in (z.sqrmirror, z.sqrtrans):
                    copies = factory(array=True)(body.right(3).forw(3))
                    centers = {(round(float(s.center().x)), round(float(s.center().y))) for s in copies}
                    self.assertEqual(centers, {(4, 4), (-4, 4), (4, -4), (-4, -4)})

    def test_removed_unit_argument_is_rejected(self):
        for factory, args in ((z.multitrans, ([],)), (z.multitransform, ([],)),
                              (z.sqrmirror, ()), (z.sqrtrans, ()),
                              (z.rotate_array, (3,)), (z.rotate_array2, (3,))):
            with self.subTest(factory=factory.__name__), self.assertRaises(TypeError):
                factory(*args, unit=True)

    def test_explicit_assembly_publishes_separate_parts(self):
        with z.using_context(z.Context.deferred(cache=False)):
            part = z.box(2).right(5)
            copies = z.rotate_array(4, array=True)(part)
            assembly = unit(parts=copies)
            with z.managed_scene(1) as scene:
                z.display(assembly)
                snapshot = z.show()
            self.assertEqual(len(snapshot.objects), 4)

    def test_foreign_context_and_invalid_transform_rejected(self):
        first = z.Context.deferred(cache=False)
        second = z.Context.deferred(cache=False)
        with self.assertRaises(ValueError):
            z.multitrans([first.call(z.transform), second.call(z.transform)])
        with self.assertRaises(TypeError):
            z.multitrans([42])
        with self.assertRaises(TypeError):
            z.multitrans([], array=1)
        self.assertEqual(z.multitrans([], array=True)(z.box(1)), [])
        with self.assertRaises(ValueError):
            z.multitrans([])(z.box(1))


if __name__ == '__main__':
    unittest.main()
