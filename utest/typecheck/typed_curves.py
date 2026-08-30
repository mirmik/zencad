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
    circle = assert_type(runtime.circle_curve(radius), typed.Curve)
    assert_type(runtime.ellipse_curve(radius + 1, radius), typed.Curve)
    assert_type(line.point(1), typed.Point3)
    assert_type(line.d0(1), typed.Point3)
    assert_type(line.value(1), typed.Point3)
    assert_type(line.tangent(1), typed.Vector3)
    assert_type(line.d1(1), typed.Vector3)
    assert_type(circle.range(), typed.Interval)
    assert_type(circle.curvetype(), typed.CurveKind)
    assert_type(line.endpoints(), tuple[typed.Point3, typed.Point3])
    assert_type(line.line_parameters(), typed.LineParameters)
    assert_type(circle.circle_parameters(), typed.CircleParameters)
    ellipse = runtime.ellipse_curve(radius + 1, radius)
    assert_type(ellipse.ellipse_parameters(), typed.EllipseParameters)
    assert_type(line.lower_distance_parameter(origin), typed.Scalar)
    assert_type(line.trimmed_edge(0, 1), typed.Edge)
    assert_type(circle.uniform(4), list[typed.Scalar])
    assert_type(circle.uniform_points(4), list[typed.Point3])
    points = (
        origin,
        origin + runtime.vector(radius, 0, 0),
        origin + runtime.vector(radius, radius, 0),
    )
    interpolated = assert_type(runtime.interpolate_curve(points), typed.Curve)
    assert_type(runtime.interpolate(points), typed.Edge)
    bezier = assert_type(runtime.bezier_curve(points), typed.Curve)
    assert_type(runtime.bezier(points), typed.Edge)
    bspline = assert_type(runtime.bspline_curve(points, (0, 1), (3, 3), 2), typed.Curve)
    assert_type(runtime.bspline(points, (0, 1), (3, 3), 2), typed.Edge)
    assert_type(interpolated.edge(), typed.Edge)
    assert_type(bezier.edge((0, 1)), typed.Edge)
    assert_type(runtime.make_edge(bspline, bspline.range()), typed.Edge)
    assert_type(circle.transform(runtime.moveX(1)), typed.Curve)

    segment = assert_type(
        runtime.segment2(runtime.point2(0, 0), runtime.point2(radius, 0)),
        typed.Curve2,
    )
    ellipse2 = assert_type(runtime.ellipse2(radius + 1, radius), typed.Curve2)
    trimmed = assert_type(runtime.trim_curve2(segment, 0, radius), typed.Curve2)
    assert_type(segment.trim(0, radius), typed.Curve2)
    assert_type(ellipse2.point(0), typed.Point2)
    assert_type(trimmed.tangent(0), typed.Vector2)
    assert_type(trimmed.range(), typed.Interval)
    assert_type(circle.unlazy(), typed.Curve)
    assert_type(trimmed.unlazy(), typed.Curve2)
