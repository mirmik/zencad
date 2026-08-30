"""Static contract for typed Shape factories and binary booleans."""

from typing_extensions import assert_type

from zencad import _typed as typed


def shape_factory_contract(runtime: typed.Runtime) -> None:
    origin = runtime.point(0, 0, 0)
    x = runtime.vector(2, 0, 0)
    y = runtime.vector(0, 3, 0)
    points = (origin, origin + x, origin + x + y, origin + y)

    assert_type(runtime.segment(origin, origin + x), typed.Edge)
    assert_type(runtime.polysegment(points, closed=True), typed.Wire)
    assert_type(runtime.polygon(points), typed.Face)
    assert_type(runtime.rectangle(2, 3), typed.Face)
    box = assert_type(runtime.box(runtime.vector(2, 3, 4)), typed.Solid)
    sphere = assert_type(runtime.sphere(box.mass()), typed.Solid)

    union = assert_type(box + sphere, typed.Shape)
    assert_type(box - sphere, typed.Shape)
    assert_type(box ^ sphere, typed.Shape)

    assert_type(box.unlazy(), typed.Solid)
    assert_type(union.unlazy(), typed.Shape)
