import math
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore
from OCP.TopAbs import TopAbs_SOLID

from zencad import _typed as typed
from zencad.operation import DomainOperation, using_context
from zencad.runtime.scene_protocol import decode_brep, encode_brep


class TypedSolidConstructorsTest(unittest.TestCase):
    def test_solid_family_is_declared_at_module_level(self):
        for name in (
            "box",
            "sphere",
            "cylinder",
            "cone",
            "torus",
            "halfspace",
            "make_solid",
        ):
            with self.subTest(operation=name):
                self.assertIsInstance(getattr(typed, name), DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        radius = context.call(typed.scalar, 2)
        sphere = typed.sphere(radius)
        with using_context(context):
            values = (
                typed.cube(2, 3, 4),
                sphere,
                typed.cylinder(2, 3),
                typed.cone(2, 1, 3),
                typed.torus(4, 1),
                typed.halfspace(),
            )
            remade = typed.make_solid(typed.box(2).shells()[0])

        self.assertTrue(all(value.context is context for value in values))
        self.assertIs(remade.context, context)
        self.assertEqual(events, [])
        self.assertAlmostEqual(float(values[0].mass()), 24.0)
        self.assertAlmostEqual(float(remade.mass()), 8.0)

    def test_exact_solid_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    values = (
                        context.call(typed.cube, 2, 3, 4, True),
                        context.call(typed.sphere, 2),
                        context.call(typed.cylinder, 2, 3, center=True),
                        context.call(typed.cone, 2, 1, 3, center=True),
                        context.call(typed.torus, 4, 1),
                        context.call(
                            typed.halfspace,
                        ),
                    )

                    policy_types = tuple(type(value) for value in values)
                    observed_types.add(policy_types)
                    self.assertEqual(policy_types, (typed.Solid,) * len(values))
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    for value in values:
                        native = value.native()
                        self.assertEqual(native.ShapeType(), TopAbs_SOLID)
                        self.assertFalse(native.IsNull())

                    cube, sphere, cylinder, cone, torus, _ = values
                    self.assertAlmostEqual(float(cube.mass()), 24.0)
                    self.assertAlmostEqual(float(sphere.mass()), 4 / 3 * math.pi * 8)
                    self.assertAlmostEqual(float(cylinder.mass()), math.pi * 12)
                    self.assertAlmostEqual(float(cone.mass()), 7 * math.pi)
                    self.assertAlmostEqual(float(torus.mass()), 8 * math.pi**2)

        self.assertEqual(len(observed_types), 1)

    def test_size_center_and_angular_variants(self):
        context = typed.Context.deferred(cache=False)

        box = context.call(typed.box, size=(2, 4, 6), center="xz")
        cube = context.call(typed.cube, size=(2, 4, 6), center=True)
        sphere = context.call(typed.sphere, 2, yaw=math.pi, pitch=(-1, 1))
        scalar_pitch_sphere = context.call(typed.sphere, 2, pitch=1)
        cylinder = context.call(typed.cylinder, 2, 3, yaw=math.pi, center=True)
        cone = context.call(typed.cone, 2, 1, 3, yaw=math.pi, center=True)
        torus = context.call(typed.torus, 4, 1, yaw=math.pi, pitch=(-0.5, 0.5))
        scalar_pitch_torus = context.call(typed.torus, 4, 1, pitch=0.5)

        self.assertEqual(box.boundbox().center.value(), (0.0, 2.0, 0.0))
        self.assertEqual(cube.boundbox().center.value(), (0.0, 0.0, 0.0))
        self.assertGreater(float(sphere.mass()), 0.0)
        self.assertLess(float(sphere.mass()), 4 / 3 * math.pi * 8)
        self.assertFalse(scalar_pitch_sphere.native().IsNull())
        self.assertAlmostEqual(float(cylinder.mass()), 6 * math.pi)
        self.assertAlmostEqual(float(cone.mass()), 3.5 * math.pi)
        self.assertFalse(torus.native().IsNull())
        self.assertFalse(scalar_pitch_torus.native().IsNull())
        self.assertAlmostEqual(float(cylinder.boundbox().center.z), 0.0)
        self.assertAlmostEqual(float(cone.boundbox().center.z), 0.0)

    def test_scalar_constructor_arguments_preserve_the_graph(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        unit = context.call(typed.box, 2).mass() / 8
        values = (
            context.call(typed.cube, unit * 2),
            context.call(
                typed.sphere, unit * 2, yaw=unit * math.pi, pitch=(-unit, unit)
            ),
            context.call(typed.cylinder, unit * 2, unit * 3, yaw=unit * math.pi),
            context.call(typed.cone, unit * 2, unit, unit * 3),
            context.call(typed.torus, unit * 4, unit),
        )

        self.assertEqual(events, [])
        self.assertEqual(tuple(type(value) for value in values), (typed.Solid,) * 5)
        self.assertTrue(all(not value.native().IsNull() for value in values))
        self.assertTrue(events)

    def test_empty_shape_is_the_topology_zero_and_is_cacheable(self):
        store = MemoryCacheStore()
        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        empty = first.call(
            typed.empty_shape,
        )
        legacy_empty = first.call(
            typed.nullshape,
        )
        solid = first.call(typed.box, 1)

        self.assertIs(type(empty), typed.Shape)
        self.assertIs(type(legacy_empty), typed.Shape)
        self.assertEqual(first_events, [])
        self.assertEqual(empty.shapetype(), "compound")
        self.assertEqual(len(empty.solids()), 0)
        self.assertAlmostEqual(float(empty.mass()), 0.0)
        self.assertTrue(empty.boundbox().is_empty())
        self.assertAlmostEqual(float((empty + solid).mass()), 1.0)
        self.assertAlmostEqual(float((solid - empty).mass()), 1.0)
        self.assertAlmostEqual(float((empty ^ solid).mass()), 0.0)
        payload = encode_brep(empty.native())
        self.assertFalse(decode_brep(payload).IsNull())
        self.assertTrue(
            any(event.kind is EvaluationEventKind.CACHE_STORE for event in first_events)
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        restored = second.call(
            typed.empty_shape,
        )
        self.assertFalse(restored.native().IsNull())
        self.assertAlmostEqual(float(restored.mass()), 0.0)
        self.assertTrue(
            any(
                event.kind is EvaluationEventKind.CACHE_HIT
                and event.operation_id == "zencad.typed.empty_shape"
                for event in second_events
            )
        )

    def test_make_solid_composes_shell_handles(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        shell = context.call(typed.box, 2).shells()[0]
        solid = context.call(typed.make_solid, shell)
        solid_from_sequence = context.call(typed.make_solid, (shell,))

        self.assertIs(type(solid), typed.Solid)
        self.assertIs(type(solid_from_sequence), typed.Solid)
        self.assertEqual(events, [])
        self.assertAlmostEqual(float(solid.mass()), 8.0)
        self.assertAlmostEqual(float(solid_from_sequence.mass()), 8.0)

    def test_invalid_solid_constructor_inputs_fail_at_the_typed_boundary(self):
        context = typed.Context.deferred(cache=False)
        other = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(TypeError, "exactly two scalar bounds"):
            context.call(typed.sphere, 1, pitch=(0, 1, 2)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "center must be bool"):
            context.call(typed.cylinder, 1, 2, center="z").native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "at least one Shell"):
            context.call(typed.make_solid, ()).native()
        with self.assertRaises(TypeError):
            context.call(typed.make_solid, (context.call(typed.box, 1),)).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "different contexts"):
            context.call(typed.make_solid, other.call(typed.box, 1).shells()[0])


if __name__ == "__main__":
    unittest.main()
