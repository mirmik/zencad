"""Static contract for typed Shape factories and binary booleans."""

from typing_extensions import assert_type

from zencad import _typed as typed


def shape_factory_contract(context: typed.Context) -> None:
    origin = context.call(typed.point, 0, 0, 0)
    x = context.call(typed.vector, 2, 0, 0)
    y = context.call(typed.vector, 0, 3, 0)
    points = (origin, origin + x, origin + x + y, origin + y)

    assert_type(context.call(typed.segment, origin, origin + x), typed.Edge)
    assert_type(context.call(typed.polysegment, points, closed=True), typed.Wire)
    assert_type(context.call(typed.polygon, points), typed.Face)
    assert_type(context.call(typed.rectangle, 2, 3), typed.Face)
    box = assert_type(
        context.call(typed.box, context.call(typed.vector, 2, 3, 4)), typed.Solid
    )
    sphere = assert_type(context.call(typed.sphere, box.mass()), typed.Solid)

    union = assert_type(box + sphere, typed.Shape)
    assert_type(box - sphere, typed.Shape)
    assert_type(box ^ sphere, typed.Shape)
