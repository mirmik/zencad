"""Static result contract for typed Curve and Curve2 handles."""

from typing_extensions import assert_type

from zencad import _typed as typed


def curve_contract(context: typed.Context) -> None:
    shape = context.call(typed.box, 2)
    radius = shape.mass() / 4
    origin = shape.center()

    line = assert_type(
        context.call(typed.line, origin, context.call(typed.vector, radius, 0, 0)),
        typed.Curve,
    )
    circle = assert_type(context.call(typed.circle_curve, 2.0), typed.Curve)
    assert_type(context.call(typed.ellipse_curve, 3.0, 2.0), typed.Curve)
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
    ellipse = context.call(typed.ellipse_curve, 3.0, 2.0)
    assert_type(ellipse.ellipse_parameters(), typed.EllipseParameters)
    assert_type(line.lower_distance_parameter(origin), typed.Scalar)
    assert_type(line.trimmed_edge(0, 1), typed.Edge)
    assert_type(circle.uniform(4), list[typed.Scalar])
    assert_type(circle.uniform_points(4), list[typed.Point3])
    points = (
        origin,
        origin + context.call(typed.vector, radius, 0, 0),
        origin + context.call(typed.vector, radius, radius, 0),
    )
    interpolated = assert_type(
        context.call(typed.interpolate_curve, points), typed.Curve
    )
    assert_type(context.call(typed.interpolate, points), typed.Edge)
    bezier = assert_type(context.call(typed.bezier_curve, points), typed.Curve)
    assert_type(context.call(typed.bezier, points), typed.Edge)
    bspline = assert_type(
        context.call(typed.bspline_curve, points, (0, 1), (3, 3), 2), typed.Curve
    )
    assert_type(context.call(typed.bspline, points, (0, 1), (3, 3), 2), typed.Edge)
    assert_type(interpolated.edge(), typed.Edge)
    assert_type(bezier.edge((0, 1)), typed.Edge)
    assert_type(context.call(typed.make_edge, bspline, bspline.range()), typed.Edge)
    assert_type(circle.transform(context.call(typed.moveX, 1)), typed.Curve)

    segment = assert_type(
        context.call(
            typed.segment2,
            context.call(typed.point2, 0, 0),
            context.call(typed.point2, radius, 0),
        ),
        typed.Curve2,
    )
    ellipse2 = assert_type(context.call(typed.ellipse2, 3.0, 2.0), typed.Curve2)
    trimmed = assert_type(
        context.call(typed.trim_curve2, segment, 0, 2.0), typed.Curve2
    )
    assert_type(segment.trim(0, radius), typed.Curve2)
    assert_type(segment.rotate(radius), typed.Curve2)
    assert_type(ellipse2.point(0), typed.Point2)
    assert_type(trimmed.tangent(0), typed.Vector2)
    assert_type(trimmed.range(), typed.Interval)


def module_curve_contract(context: typed.Context) -> None:
    origin = context.call(typed.point3, 0, 0, 0)
    second = context.call(typed.point3, 1, 0, 0)
    third = context.call(typed.point3, 1, 1, 0)
    points = (origin, second, third)

    line = assert_type(
        typed.line(origin, context.call(typed.vector3, 1, 0, 0)), typed.Curve
    )
    circle = assert_type(typed.circle_curve(2), typed.Curve)
    assert_type(typed.ellipse_curve(2, 1), typed.Curve)
    assert_type(typed.interpolate_curve(points), typed.Curve)
    assert_type(typed.interpolate(points), typed.Edge)
    assert_type(typed.bezier_curve(points), typed.Curve)
    assert_type(typed.bezier(points), typed.Edge)
    assert_type(typed.bspline_curve(points, (0, 1), (3, 3), 2), typed.Curve)
    assert_type(typed.bspline(points, (0, 1), (3, 3), 2), typed.Edge)
    edge = assert_type(typed.make_edge(circle), typed.Edge)
    assert_type(typed.circle_arc(*points), typed.Edge)
    assert_type(typed.segment(origin, second), typed.Edge)
    assert_type(typed.make_wire(edge), typed.Wire)
    assert_type(typed.polysegment(points), typed.Wire)
    assert_type(typed.rounded_polysegment(points, 0.1), typed.Wire)
    assert_type(typed.helix(1, 2, step=0.5), typed.Wire)
    curve2 = assert_type(
        typed.segment2(
            context.call(typed.point2, 0, 0), context.call(typed.point2, 1, 0)
        ),
        typed.Curve2,
    )
    assert_type(typed.ellipse2(2, 1), typed.Curve2)
    assert_type(typed.trim_curve2(curve2, 0, 1), typed.Curve2)
    assert_type(line.edge(), typed.Edge)
