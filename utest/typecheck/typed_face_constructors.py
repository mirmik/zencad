"""Static contracts for root-compatible typed 2D constructors."""

from typing_extensions import assert_type

from zencad import _typed as typed


def face_constructor_contract(runtime: typed.Runtime) -> None:
    points = (
        runtime.point3(0, 0, 0),
        runtime.point3(4, 0, 0),
        runtime.point3(4, 3, 0),
        runtime.point3(0, 3, 0),
    )
    assert_type(runtime.circle_curve(2), typed.Curve)
    assert_type(runtime.ellipse_curve(4, 2), typed.Curve)
    assert_type(runtime.circle(2), typed.Face)
    assert_type(runtime.circle(2, wire=True), typed.Edge)
    assert_type(runtime.circle(2, (0, 1)), typed.Face)
    assert_type(runtime.ellipse(4, 2), typed.Face)
    assert_type(runtime.ellipse(4, 2, wire=True), typed.Edge)
    assert_type(runtime.polygon(points), typed.Face)
    assert_type(runtime.polygon(points, True), typed.Wire)
    assert_type(runtime.rectangle(4, 3), typed.Face)
    assert_type(runtime.rectangle(4, 3, wire=True), typed.Wire)
    assert_type(runtime.rectangle_wire(4, 3), typed.Wire)
    assert_type(runtime.square(4), typed.Face)
    assert_type(runtime.square(4, wire=True), typed.Wire)
    assert_type(runtime.ngon(4, 6), typed.Face)
    assert_type(runtime.ngon(4, 6, True), typed.Wire)
    wire = runtime.rectangle_wire(4, 3)
    face = assert_type(runtime.fill(wire), typed.Face)
    assert_type(runtime.fix_face(face), typed.Face)
    assert_type(runtime.infplane(), typed.Face)
    assert_type(
        runtime.ruled(
            runtime.segment(points[0], points[1]),
            runtime.segment(points[3], points[2]),
        ),
        typed.Face,
    )
    assert_type(
        runtime.interpolate2(((points[0], points[1]), (points[3], points[2]))),
        typed.Face,
    )
