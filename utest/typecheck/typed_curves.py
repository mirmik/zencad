"""Static result contract for typed Curve and Curve2 handles."""

from typing_extensions import assert_type

from zencad import _typed as typed


def curve_contract(runtime: typed.Runtime) -> None:
    shape = runtime.box(2)
    radius = shape.mass() / 4
    origin = shape.center()

    line = assert_type(
        runtime.line(origin, runtime.vector(radius, 0, 0)),
        typed.Curve,
    )
    circle = assert_type(runtime.circle(radius), typed.Curve)
    assert_type(runtime.ellipse(radius + 1, radius), typed.Curve)
    assert_type(line.point(1), typed.Point3)
    assert_type(line.tangent(1), typed.Vector3)
    assert_type(circle.range(), tuple[typed.Scalar, typed.Scalar])

    segment = assert_type(
        runtime.segment2(runtime.point2(0, 0), runtime.point2(radius, 0)),
        typed.Curve2,
    )
    ellipse2 = assert_type(runtime.ellipse2(radius + 1, radius), typed.Curve2)
    trimmed = assert_type(runtime.trim_curve2(segment, 0, radius), typed.Curve2)
    assert_type(segment.trim(0, radius), typed.Curve2)
    assert_type(ellipse2.point(0), typed.Point2)
    assert_type(trimmed.tangent(0), typed.Vector2)
    assert_type(trimmed.range(), tuple[typed.Scalar, typed.Scalar])
    assert_type(circle.unlazy(), typed.Curve)
    assert_type(trimmed.unlazy(), typed.Curve2)
