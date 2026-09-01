"""Static contract for decorator-declared typed operations."""

from typing_extensions import assert_type

from zencad import _typed as typed
from zencad._typed.context import Context


def operation_contract(context: Context) -> None:
    assert_type(context, Context)
    direct = assert_type(typed.box(1, 2, 3), typed.Solid)
    forwarded = assert_type(context.call(typed.box, 1, 2, 3), typed.Solid)
    radius = context.call(typed.scalar, 2)

    assert_type(typed.cube(1), typed.Solid)
    assert_type(typed.sphere(radius), typed.Solid)
    assert_type(typed.cylinder(radius, 3), typed.Solid)
    assert_type(typed.cone(radius, 1, 3), typed.Solid)
    assert_type(typed.torus(radius, 1), typed.Solid)
    assert_type(typed.halfspace(), typed.Solid)
    assert_type(
        typed.make_solid(context.call(typed.box, 1).shells()[0]),
        typed.Solid,
    )
    assert_type(typed.split(direct, typed.infplane()), typed.SplitResult)
    assert_type(typed.slice(direct, z=1), typed.SliceResult)
    assert_type(
        context.call(typed.split, direct, context.call(typed.infplane)),
        typed.SplitResult,
    )
    assert_type(context.call(typed.slice, direct, z=1), typed.SliceResult)
    assert_type(
        typed.draft(direct, direct.faces()[0], 0.05),
        typed.Solid,
    )
    assert_type(
        context.call(typed.draft, direct, direct.faces()[0], 0.05),
        typed.Solid,
    )

    assert_type(direct + forwarded, typed.Shape)
    assert_type(direct.mass() + 1, typed.Scalar)
