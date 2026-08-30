"""Static contract for the legacy value and transform compatibility slice."""

from typing_extensions import assert_type

from zencad import _typed as typed


def value_transform_compatibility(runtime: typed.Runtime) -> None:
    scalar = runtime.scalar(1)
    point = assert_type(runtime.point3(1, scalar), typed.Point3)
    vector = assert_type(runtime.vector3((1, 2, 3)), typed.Vector3)
    quaternion = assert_type(runtime.quat((0, 0, 0, 1)), typed.Quaternion)

    assert_type(point.to_vector3(), typed.Vector3)
    assert_type(vector.to_point3(), typed.Point3)
    assert_type(point.cross(vector), typed.Vector3)
    assert_type(point.distance(point), typed.Scalar)
    assert_type(vector.angle(vector), typed.Scalar)
    assert_type(vector.normalize(), typed.Vector3)

    transform = assert_type(runtime.move(vector), typed.Transform)
    assert_type(runtime.translate(1, scalar, 3), typed.Transform)
    assert_type(runtime.right(scalar), typed.Transform)
    assert_type(runtime.forw(scalar), typed.Transform)
    assert_type(runtime.up(scalar), typed.Transform)
    assert_type(runtime.rotate(vector, scalar), typed.Transform)
    assert_type(runtime.rotate(vector), typed.Transform)
    assert_type(runtime.rotate_quat(quaternion), typed.Transform)
    assert_type(runtime.rotateX(scalar), typed.Transform)
    assert_type(runtime.mirrorXY(), typed.Transform)
    assert_type(runtime.mirrorX(), typed.Transform)
    assert_type(runtime.mirrorO(point), typed.Transform)

    assert_type(transform.transform_point(point), typed.Point3)
    assert_type(transform.transform_vector(vector), typed.Vector3)
    assert_type(transform.inverse_transform_point(point), typed.Point3)
    assert_type(transform.inverse_transform_vector(vector), typed.Vector3)
    assert_type(transform.rotation_quat(), typed.Quaternion)

    solid = runtime.box(1)
    assert_type(solid.move(vector), typed.Solid)
    assert_type(solid.mov(1, 2, scalar), typed.Solid)
    assert_type(solid.right(scalar).forw(2).up(3), typed.Solid)
    assert_type(solid.rotate(vector, scalar), typed.Solid)
    assert_type(solid.rotZ(scalar), typed.Solid)
    assert_type(solid.scale(scalar, point), typed.Solid)
    assert_type(solid.mirrorXY(), typed.Solid)
