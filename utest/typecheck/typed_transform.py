"""Static result-type table for typed quaternions and transforms."""

from typing_extensions import assert_type

from zencad import _typed as typed


Matrix4x4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]


def transform_algebra(runtime: typed.Runtime) -> None:
    scalar = runtime.scalar(0.5)
    point = runtime.point(1, 2, 3)
    vector = runtime.vector(0, 0, 1)

    quaternion = assert_type(runtime.quaternion(0, 0, 0, 1), typed.Quaternion)
    axis_angle = assert_type(
        runtime.quaternion_axis_angle(vector, scalar), typed.Quaternion
    )
    assert_type(
        typed.Quaternion((0, 0, scalar, 1), runtime=runtime),
        typed.Quaternion,
    )
    assert_type(typed.Quaternion.identity(runtime=runtime), typed.Quaternion)

    assert_type(quaternion.x, typed.Scalar)
    assert_type(quaternion.y, typed.Scalar)
    assert_type(quaternion.z, typed.Scalar)
    assert_type(quaternion.w, typed.Scalar)
    assert_type(quaternion * axis_angle, typed.Quaternion)
    assert_type(quaternion.then(axis_angle), typed.Quaternion)
    assert_type(quaternion.conjugate(), typed.Quaternion)
    assert_type(quaternion.inverse(), typed.Quaternion)
    assert_type(quaternion.normalized(), typed.Quaternion)
    assert_type(quaternion.norm(), typed.Scalar)
    assert_type(quaternion.rotate(vector), typed.Vector3)
    assert_type(quaternion.to_transform(), typed.Transform)
    assert_type(quaternion.value(), tuple[float, float, float, float])

    identity = assert_type(runtime.identity_transform(), typed.Transform)
    assert_type(typed.Transform(runtime=runtime), typed.Transform)
    translation = assert_type(runtime.translation(vector), typed.Transform)
    assert_type(runtime.translation(1, scalar, 3), typed.Transform)
    rotation = assert_type(runtime.rotation(quaternion), typed.Transform)
    assert_type(runtime.rotation(vector, scalar), typed.Transform)
    scaling = assert_type(runtime.scale(scalar), typed.Transform)
    assert_type(runtime.scale(scalar, center=point), typed.Transform)
    reflection = assert_type(runtime.mirror(vector), typed.Transform)
    assert_type(runtime.mirror(vector, origin=point), typed.Transform)

    assert_type(translation.scale, typed.Scalar)
    assert_type(rotation.rotation, typed.Quaternion)
    assert_type(translation.translation, typed.Vector3)
    assert_type(identity * translation, typed.Transform)
    assert_type(translation.then(rotation), typed.Transform)
    assert_type(scaling.inverse(), typed.Transform)
    assert_type(reflection.apply(point), typed.Point3)
    assert_type(reflection.apply(vector), typed.Vector3)
    assert_type(reflection(point), typed.Point3)
    assert_type(reflection(vector), typed.Vector3)
    assert_type(identity.matrix(), Matrix4x4)

    shape = runtime.box(1)
    assert_type(shape.transform(translation), typed.Solid)
