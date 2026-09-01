"""Static contracts for root-compatible typed 2D constructors."""

from typing_extensions import assert_type

from zencad import _typed as typed


def face_constructor_contract(context: typed.Context) -> None:
    points = (
        context.call(typed.point3, 0, 0, 0),
        context.call(typed.point3, 4, 0, 0),
        context.call(typed.point3, 4, 3, 0),
        context.call(typed.point3, 0, 3, 0),
    )
    assert_type(context.call(typed.circle_curve, 2), typed.Curve)
    assert_type(context.call(typed.ellipse_curve, 4, 2), typed.Curve)
    assert_type(context.call(typed.circle, 2), typed.Face)
    assert_type(context.call(typed.circle, 2, wire=True), typed.Edge)
    assert_type(context.call(typed.circle, 2, (0, 1)), typed.Face)
    assert_type(context.call(typed.ellipse, 4, 2), typed.Face)
    assert_type(context.call(typed.ellipse, 4, 2, wire=True), typed.Edge)
    assert_type(context.call(typed.polygon, points), typed.Face)
    assert_type(context.call(typed.polygon, points, True), typed.Wire)
    assert_type(context.call(typed.rectangle, 4, 3), typed.Face)
    assert_type(context.call(typed.rectangle, 4, 3, wire=True), typed.Wire)
    assert_type(context.call(typed.rectangle_wire, 4, 3), typed.Wire)
    assert_type(context.call(typed.square, 4), typed.Face)
    assert_type(context.call(typed.square, 4, wire=True), typed.Wire)
    assert_type(context.call(typed.ngon, 4, 6), typed.Face)
    assert_type(context.call(typed.ngon, 4, 6, True), typed.Wire)
    wire = context.call(typed.rectangle_wire, 4, 3)
    face = assert_type(context.call(typed.fill, wire), typed.Face)
    assert_type(context.call(typed.fix_face, face), typed.Face)
    assert_type(
        context.call(
            typed.infplane,
        ),
        typed.Face,
    )
    assert_type(
        context.call(
            typed.ruled,
            context.call(typed.segment, points[0], points[1]),
            context.call(typed.segment, points[3], points[2]),
        ),
        typed.Face,
    )
    assert_type(
        context.call(
            typed.interpolate2, ((points[0], points[1]), (points[3], points[2]))
        ),
        typed.Face,
    )
    assert_type(
        context.call(
            typed.widewire, context.call(typed.segment, points[0], points[1]), 1
        ),
        typed.Shape,
    )

    assert_type(typed.circle(2), typed.Face)
    assert_type(typed.circle(2, wire=True), typed.Edge)
    assert_type(typed.ellipse(4, 2), typed.Face)
    assert_type(typed.ellipse(4, 2, wire=True), typed.Edge)
    assert_type(typed.polygon(points), typed.Face)
    assert_type(typed.polygon(points, True), typed.Wire)
    assert_type(typed.rectangle(4, 3), typed.Face)
    assert_type(typed.rectangle(4, 3, wire=True), typed.Wire)
    assert_type(typed.rectangle_wire(4, 3), typed.Wire)
    assert_type(typed.square(4), typed.Face)
    assert_type(typed.square(4, wire=True), typed.Wire)
    assert_type(typed.ngon(4, 6), typed.Face)
    assert_type(typed.ngon(4, 6, True), typed.Wire)
    module_face = assert_type(typed.fill(wire), typed.Face)
    assert_type(typed.fix_face(module_face), typed.Face)
    assert_type(typed.infplane(), typed.Face)
    assert_type(
        typed.ruled(
            context.call(typed.segment, points[0], points[1]),
            context.call(typed.segment, points[3], points[2]),
        ),
        typed.Face,
    )
    assert_type(
        typed.interpolate2(((points[0], points[1]), (points[3], points[2]))),
        typed.Face,
    )
    assert_type(
        typed.widewire(context.call(typed.segment, points[0], points[1]), 1),
        typed.Shape,
    )
