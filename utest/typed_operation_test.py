import inspect
from typing import get_type_hints
import unittest

import evalcache

import zencad
import zencad.operation as operation_module
from zencad import _typed as typed
from zencad._typed.topology import SHAPE_SPEC
from zencad.operation import DomainOperation, operation, using_context


def _selected_shape_type(args, kwargs):
    if kwargs.get("exact", False):
        return type(args[0])
    return typed.Shape


def _selected_shape_result(args, kwargs):
    if kwargs.get("exact", False):
        return args[0]._result_spec
    return SHAPE_SPEC


@operation(
    result=SHAPE_SPEC,
    returns=_selected_shape_type,
    select_result=_selected_shape_result,
    operation_id="zencad.test.selected_shape",
)
def _selected_shape(shape: typed.Shape, *, exact: bool = False) -> typed.Shape:
    del exact
    return shape


class TypedOperationTest(unittest.TestCase):
    def test_preparer_dsl_is_not_part_of_the_operation_api(self):
        self.assertFalse(hasattr(operation_module, "OperationArguments"))
        self.assertFalse(hasattr(operation_module, "arguments"))
        self.assertNotIn(
            "backend", inspect.signature(operation_module.operation).parameters
        )

    def test_context_owns_policy_without_becoming_a_cad_facade(self):
        context = typed.Context.deferred(cache=False)

        self.assertFalse(hasattr(type(context), "box"))
        with typed.using_context(context):
            size = typed.scalar(2)
            origin = typed.point3()
            direction = typed.vector3(0, 0, size)
            shape = typed.box(2).translate(direction)
            face = typed.rectangle(size, size, center=True)
            extruded = typed.extrude(face, size, center=True)
            wire = typed.WireBuilder(context=context).l(1, 0).l(0, 1).build()

        self.assertIs(type(shape), typed.Solid)
        self.assertIs(shape.context, context)
        self.assertIs(origin.context, context)
        self.assertIs(extruded.context, context)
        self.assertIs(wire.context, context)
        self.assertAlmostEqual(shape.mass().value(), 8)

    def test_module_operation_and_context_shim_share_the_same_graph_contract(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )

        with using_context(context):
            direct = typed.box(2, 3, 4)
        forwarded = context.call(typed.box, 2, 3, 4)

        self.assertIs(type(direct), typed.Solid)
        self.assertIs(type(forwarded), typed.Solid)
        self.assertIs(direct.context, context)
        self.assertIs(forwarded.context, context)
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

    def test_solid_primitive_is_an_ordinary_executable_implementation(self):
        declaration = typed.cone

        self.assertFalse(hasattr(declaration, "prepare"))
        self.assertEqual(
            tuple(inspect.signature(declaration).parameters),
            ("r1", "r2", "h", "yaw", "center"),
        )
        self.assertIs(get_type_hints(declaration.function)["r1"], float)

        resolved = declaration.function(3.0, 1.0, 5.0)

        self.assertIs(type(resolved), typed.Solid)
        self.assertNotIsInstance(resolved._state, evalcache.Expression)
        self.assertGreater(float(resolved.mass()), 0)

    def test_decorated_scalar_operation_keeps_immediate_constant_folding(self):
        events = []
        context = typed.Context.immediate(
            cache=False,
            progress_hooks=(events.append,),
        )
        left = context.call(typed.scalar, 2)

        result = left + 3

        self.assertIs(type(result), typed.Scalar)
        self.assertNotIsInstance(result._state, evalcache.Expression)
        self.assertEqual(float(result), 5.0)
        self.assertEqual(events, [])

    def test_operation_rejects_handles_from_different_contexts(self):
        first = typed.Context.deferred(cache=False)
        second = typed.Context.deferred(cache=False)

        with self.assertRaisesRegex(ValueError, "different contexts"):
            _ = first.call(typed.box, 1) + second.call(typed.box, 1)

    def test_result_adapter_can_preserve_or_select_a_domain_subtype(self):
        context = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 1)

        preserved = _selected_shape(shape)
        selected = _selected_shape(shape, exact=True)

        self.assertIs(type(preserved), typed.Shape)
        self.assertIs(type(selected), typed.Solid)
        self.assertEqual(preserved._state.operation_id, "zencad.test.selected_shape")
        self.assertEqual(preserved._state.result.type_id, "zencad.typed.Shape.v1")
        self.assertEqual(selected._state.result.type_id, "zencad.typed.Solid.v1")
        self.assertFalse(selected.native().IsNull())

    def test_public_geometry_does_not_expose_the_legacy_lazy_contract(self):
        self.assertFalse(hasattr(zencad, "lazy"))
        self.assertNotIsInstance(zencad.box(1), evalcache.LazyObject)


if __name__ == "__main__":
    unittest.main()
