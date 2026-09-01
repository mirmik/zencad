"""Static contract for typed boundary boxes and structured ranges."""

from typing_extensions import assert_type

from zencad import _typed as typed


def bounds_contract(runtime: typed.Runtime, shape: typed.Shape) -> None:
    minimum = runtime.point(0, 0, 0)
    maximum = runtime.point(1, 2, 3)
    bounds = assert_type(
        runtime.boundary_box(minimum, maximum),
        typed.BoundaryBox,
    )
    assert_type(typed.boundary_box(minimum, maximum), typed.BoundaryBox)
    assert_type(typed.empty_boundary_box(), typed.BoundaryBox)
    assert_type(typed.boundbox(shape), typed.BoundaryBox)

    assert_type(runtime.empty_boundary_box(), typed.BoundaryBox)
    assert_type(shape.boundbox(), typed.BoundaryBox)
    assert_type(shape.bbox(), typed.BoundaryBox)
    assert_type(bounds.union(shape.boundbox()), typed.BoundaryBox)
    assert_type(bounds.add(shape.boundbox()), typed.BoundaryBox)
    assert_type(bounds.is_empty(), bool)
    assert_type(bounds.xmin, typed.Scalar)
    assert_type(bounds.xmax, typed.Scalar)
    assert_type(bounds.minimum, typed.Point3)
    assert_type(bounds.maximum, typed.Point3)
    assert_type(bounds.size, typed.Vector3)
    assert_type(bounds.center, typed.Point3)
    interval = assert_type(bounds.x_range(), typed.Interval)
    assert_type(bounds.xrange(), typed.Interval)
    assert_type(bounds.y_range(), typed.Interval)
    assert_type(bounds.yrange(), typed.Interval)
    assert_type(bounds.z_range(), typed.Interval)
    assert_type(bounds.zrange(), typed.Interval)
    assert_type(bounds.xlength(), typed.Scalar)
    assert_type(bounds.ylength(), typed.Scalar)
    assert_type(bounds.zlength(), typed.Scalar)
    assert_type(bounds.shape(), typed.Solid)
    assert_type(interval.lower, typed.Scalar)
    assert_type(interval.upper, typed.Scalar)
    assert_type(interval.length(), typed.Scalar)
    assert_type(interval.value(), tuple[float, float])
    assert_type(bounds.value(), typed.BoundaryBoxRecord)
    assert_type(bounds.unlazy(), typed.BoundaryBox)
