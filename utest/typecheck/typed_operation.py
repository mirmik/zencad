"""Static contract for decorator-declared typed operations."""

from typing_extensions import assert_type

from zencad import geom as typed
from zencad.geom.context import Context


def operation_contract(context: Context) -> None:
    assert_type(context, Context)
    direct = assert_type(typed.box(1, 2, 3), typed.Solid)
    forwarded = assert_type(context.call(typed.box, 1, 2, 3), typed.Solid)
    assert_type(typed.cube(1), typed.Solid)
    assert_type(typed.sphere(2.0), typed.Solid)
    assert_type(typed.cylinder(2.0, 3.0), typed.Solid)
    assert_type(typed.cone(2.0, 1.0, 3.0), typed.Solid)
    assert_type(typed.torus(2.0, 1.0), typed.Solid)
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
