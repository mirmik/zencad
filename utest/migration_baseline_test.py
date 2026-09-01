import unittest

import evalcache
from evalcache.v2 import MemoryCacheStore

import zencad


class PublicDomainCutoverTest(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_root_geometry_is_the_typed_domain_api(self):
        shape = zencad.box(2)

        self.assertIs(type(shape), zencad.Solid)
        self.assertNotIsInstance(shape, evalcache.LazyObject)
        self.assertFalse(hasattr(zencad, "Runtime"))
        self.assertFalse(hasattr(zencad, "RuntimeCompatibility"))
        self.assertFalse(hasattr(zencad, "lazy"))

    def test_context_owns_policy_without_becoming_a_cad_facade(self):
        context = zencad.Context.deferred(cache=False)

        self.assertFalse(hasattr(context, "box"))
        with zencad.using_context(context):
            shape = zencad.box(2).translate(1, 2, 3)

        self.assertIs(shape.context, context)
        self.assertAlmostEqual(float(shape.mass()), 8.0)

    def test_repeated_graphs_have_stable_expression_digests(self):
        first = zencad.box(3) - zencad.sphere(1)
        second = zencad.box(3) - zencad.sphere(1)

        self.assertEqual(first._state.digest, second._state.digest)
        self.assertFalse(first.native().IsNull())

    def test_cache_round_trip_restores_a_domain_handle(self):
        store = MemoryCacheStore()
        first = zencad.Context.deferred(cache=True, cache_store=store)
        first_shape = first.call(zencad.box, 4)
        first_shape.native()

        second = zencad.Context.deferred(cache=True, cache_store=store)
        restored = second.call(zencad.box, 4)

        self.assertIs(type(restored), zencad.Solid)
        self.assertAlmostEqual(float(restored.mass()), 64.0)

    def test_handles_from_different_contexts_cannot_mix(self):
        first = zencad.Context.deferred(cache=False)
        second = zencad.Context.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different contexts"):
            first.call(zencad.union, (first.call(zencad.box, 1), second.call(zencad.box, 1)))


if __name__ == "__main__":
    unittest.main()
