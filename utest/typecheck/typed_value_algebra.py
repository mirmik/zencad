"""Static result-type table for private typed value algebra."""

from typing import assert_type

from zencad import _typed as typed


def algebra(runtime: typed.Runtime) -> None:
    scalar = assert_type(runtime.scalar(2), typed.Scalar)
    point2 = assert_type(runtime.point2(1, 2), typed.Point2)
    vector2 = assert_type(runtime.vector2(1, 2), typed.Vector2)
    point3 = assert_type(runtime.point(1, 2, 3), typed.Point3)
    vector3 = assert_type(runtime.vector(1, 2, 3), typed.Vector3)

    assert_type(scalar + 1, typed.Scalar)
    assert_type(1 + scalar, typed.Scalar)
    assert_type(scalar * vector2, typed.Vector2)
    assert_type(scalar * vector3, typed.Vector3)

    assert_type(vector2 + vector2, typed.Vector2)
    assert_type(point2 + vector2, typed.Point2)
    assert_type(vector2 + point2, typed.Point2)
    assert_type(point2 - point2, typed.Vector2)
    assert_type(point2 - vector2, typed.Point2)
    assert_type(vector2.dot(vector2), typed.Scalar)
    assert_type(vector2.cross(vector2), typed.Scalar)

    assert_type(vector3 + vector3, typed.Vector3)
    assert_type(point3 + vector3, typed.Point3)
    assert_type(vector3 + point3, typed.Point3)
    assert_type(point3 - point3, typed.Vector3)
    assert_type(point3 - vector3, typed.Point3)
    assert_type(vector3.dot(vector3), typed.Scalar)
    assert_type(vector3.cross(vector3), typed.Vector3)
    assert_type(vector3.normalized(), typed.Vector3)
    assert_type(point3.distance_to(point3), typed.Scalar)

    assert_type(typed.sin(scalar), typed.Scalar)
    assert_type(typed.sqrt(scalar), typed.Scalar)
    assert_type(typed.atan2(scalar, 1), typed.Scalar)
