import runpy
import unittest
from pathlib import Path
from importlib import import_module

import evalcache
from evalcache.v2 import MemoryCacheStore

import zencad
import zencad._typed as typed_compat
import zencad.geom as geom
import zencad.geom.boolops as boolops_module
import zencad.geom.curve as curve_module
import zencad.geom.face as face_module
import zencad.geom.mesh as mesh_module
import zencad.geom.operations as operations_module
import zencad.geom.solid as solid_module
import zencad.geom.surface as surface_module
import zencad.geom.trans as trans_module

sweep_module = import_module("zencad.geom.sweep")


class PublicDomainCutoverTest(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_root_geometry_is_the_geom_domain_api(self):
        shape = zencad.box(2)

        self.assertIs(type(shape), zencad.Solid)
        self.assertNotIsInstance(shape, evalcache.LazyObject)
        self.assertFalse(hasattr(zencad, "Runtime"))
        self.assertFalse(hasattr(zencad, "RuntimeCompatibility"))
        self.assertFalse(hasattr(zencad, "lazy"))

    def test_geom_owns_the_canonical_implementation(self):
        self.assertIs(zencad.cylinder, geom.cylinder)
        self.assertIs(geom.cylinder, solid_module.cylinder)
        self.assertIs(typed_compat.cylinder, geom.cylinder)
        self.assertEqual(
            solid_module.cylinder.function.__module__,
            "zencad.geom.solid",
        )

    def test_historical_geom_modules_resolve_to_domain_implementations(self):
        colliding_modules = {
            name: import_module(f"zencad.geom.{name}")
            for name in ("offset", "platonic", "project", "sew", "sweep", "unify")
        }
        aliases = (
            (boolops_module.union, geom.union),
            (curve_module.circle_curve, geom.circle_curve),
            (face_module.circle, geom.circle),
            (mesh_module.to_mesh, geom.to_mesh),
            (operations_module.fillet, geom.fillet),
            (surface_module.cylinder_surface, geom.cylinder_surface),
            (sweep_module.extrude, geom.extrude),
            (trans_module.translate, geom.translate),
            (colliding_modules["offset"].offset, geom.offset),
            (colliding_modules["platonic"].platonic, geom.platonic),
            (colliding_modules["project"].project, geom.project),
            (colliding_modules["sew"].sew, geom.sew),
            (colliding_modules["sweep"].sweep, geom.sweep),
            (colliding_modules["unify"].unify, geom.unify),
        )
        for historical, canonical in aliases:
            with self.subTest(operation=canonical):
                self.assertIs(historical, canonical)

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
            first.call(
                zencad.union, (first.call(zencad.box, 1), second.call(zencad.box, 1))
            )

    def test_legacy_cup_example_keeps_vertical_handle(self):
        published = []
        example = Path(zencad.exampledir) / "Models" / "cup.py"

        with zencad.managed_scene(1, published.append):
            namespace = runpy.run_path(str(example), run_name="__main__")

        bounds = namespace["spine"].bbox().value()
        self.assertAlmostEqual(bounds.ymax - bounds.ymin, 0, places=5)
        self.assertGreater(bounds.zmax - bounds.zmin, 60)
        self.assertGreater(
            namespace["hole"].bbox().value().zmax,
            namespace["base"].bbox().value().zmax,
        )
        self.assertEqual(len(namespace["body"].solids()), 1)
        self.assertEqual(len(namespace["handle"].solids()), 1)
        cup_solids = namespace["cup"].solids()
        self.assertEqual(len(cup_solids), 1)
        self.assertGreater(cup_solids[0].mass().value(), 0)
        self.assertGreater(namespace["cup"].mass().value(), 0)
        self.assertEqual(len(published), 1)


if __name__ == "__main__":
    unittest.main()
