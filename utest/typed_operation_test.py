import inspect
import unittest

import evalcache

import zencad
from zencad import _typed as typed
from zencad._typed.topology import SHAPE_SPEC
from zencad.operation import DomainOperation, arguments, operation, using_runtime


def _identity_shape(value):
    return value


def _selected_shape_type(args, kwargs):
    if kwargs.get("exact", False):
        return type(args[0])
    return typed.Shape


def _selected_shape_result(args, kwargs):
    if kwargs.get("exact", False):
        return args[0]._result_spec
    return SHAPE_SPEC


@operation(
    backend=_identity_shape,
    result=SHAPE_SPEC,
    returns=_selected_shape_type,
    select_result=_selected_shape_result,
    operation_id="zencad.test.selected_shape",
)
def _selected_shape(shape, *, exact=False):
    del exact
    return arguments(shape)


class TypedOperationTest(unittest.TestCase):
    def test_context_owns_policy_without_becoming_a_cad_facade(self):
        context = typed.Context.deferred(cache=False)

        self.assertFalse(hasattr(type(context), "box"))
        with typed.using_context(context):
            size = typed.scalar(2)
            origin = typed.point3()
            direction = typed.vector3(0, 0, size)
            shape = typed.box(size).translate(direction)
            face = typed.rectangle(size, size, center=True)
            extruded = typed.extrude(face, size, center=True)
            wire = typed.WireBuilder(runtime=context).l(1, 0).l(0, 1).build()

        self.assertIs(type(shape), typed.Solid)
        self.assertIs(shape.runtime, context)
        self.assertIs(origin.runtime, context)
        self.assertIs(extruded.runtime, context)
        self.assertIs(wire.runtime, context)
        self.assertAlmostEqual(shape.mass().value(), 8)

    def test_module_operation_and_runtime_shim_share_the_same_graph_contract(self):
        events = []
        runtime = typed.Runtime.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )

        with using_runtime(runtime):
            direct = typed.box(2, 3, 4)
        forwarded = runtime.box(2, 3, 4)

        self.assertIs(type(direct), typed.Solid)
        self.assertIs(type(forwarded), typed.Solid)
        self.assertIs(direct.runtime, runtime)
        self.assertIs(forwarded.runtime, runtime)
        self.assertIsInstance(direct._state, evalcache.Expression)
        self.assertEqual(direct._state.operation_id, "zencad.typed.box")
        self.assertEqual(events, [])
        self.assertAlmostEqual(float(direct.mass()), 24.0)

    def test_operation_metadata_and_public_signature_live_on_the_declaration(self):
        declaration = typed.box

        self.assertIsInstance(declaration, DomainOperation)
        self.assertEqual(declaration.backend.operation_id, "zencad.typed.box")
        self.assertIs(
            inspect.signature(declaration).return_annotation,
            typed.Solid,
        )
        self.assertIn("size", inspect.signature(declaration).parameters)

    def test_decorated_scalar_operation_keeps_immediate_constant_folding(self):
        events = []
        runtime = typed.Runtime.immediate(
            cache=False,
            progress_hooks=(events.append,),
        )
        left = runtime.scalar(2)

        result = left + 3

        self.assertIs(type(result), typed.Scalar)
        self.assertNotIsInstance(result._state, evalcache.Expression)
        self.assertEqual(float(result), 5.0)
        self.assertEqual(events, [])

    def test_operation_rejects_handles_from_different_runtimes(self):
        first = typed.Runtime.deferred(cache=False)
        second = typed.Runtime.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different typed runtimes"):
            _ = first.box(1) + second.box(1)

    def test_result_adapter_can_preserve_or_select_a_domain_subtype(self):
        runtime = typed.Runtime.deferred(cache=False)
        shape = runtime.box(1)

        preserved = _selected_shape(shape)
        selected = _selected_shape(shape, exact=True)

        self.assertIs(type(preserved), typed.Shape)
        self.assertIs(type(selected), typed.Solid)
        self.assertEqual(preserved._state.operation_id, "zencad.test.selected_shape")
        self.assertEqual(preserved._state.result.type_id, "zencad.typed.Shape.v1")
        self.assertEqual(selected._state.result.type_id, "zencad.typed.Solid.v1")
        self.assertFalse(selected.native().IsNull())

    def test_bare_operation_preserves_legacy_lazy_contract(self):
        @zencad.operation
        def doubled(value):
            return value * 2

        @zencad.lazy
        def incremented(value):
            return value + 1

        doubled_value = doubled(21)
        incremented_value = incremented(41)

        self.assertIsInstance(doubled_value, evalcache.LazyObject)
        self.assertIsInstance(incremented_value, evalcache.LazyObject)
        self.assertEqual(evalcache.unlazy(doubled_value), 42)
        self.assertEqual(evalcache.unlazy(incremented_value), 42)


if __name__ == "__main__":
    unittest.main()
