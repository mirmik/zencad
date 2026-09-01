"""Static result-type table for typed quaternions and transforms."""

from typing_extensions import assert_type

from zencad import _typed as typed


Matrix4x4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]


def transform_algebra(context: typed.Context) -> None:
    scalar = context.call(typed.scalar, 0.5)
    point = context.call(typed.point, 1, 2, 3)
    vector = context.call(typed.vector, 0, 0, 1)

    quaternion = assert_type(
        context.call(typed.quaternion, 0, 0, 0, 1), typed.Quaternion
    )
    axis_angle = assert_type(
        context.call(typed.quaternion_axis_angle, vector, scalar), typed.Quaternion
    )
    assert_type(
        typed.Quaternion((0, 0, scalar, 1), context=context),
        typed.Quaternion,
    )
    assert_type(typed.Quaternion.identity(context=context), typed.Quaternion)
    assert_type(typed.quaternion(0, 0, 0, 1), typed.Quaternion)
    assert_type(typed.quaternion_axis_angle(vector, scalar), typed.Quaternion)

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

    identity = assert_type(
        context.call(
            typed.identity_transform,
        ),
        typed.Transform,
    )
    assert_type(typed.identity_transform(), typed.Transform)
    assert_type(typed.Transform(context=context), typed.Transform)
    translation = assert_type(context.call(typed.translation, vector), typed.Transform)
    assert_type(context.call(typed.translation, 1, scalar, 3), typed.Transform)
    assert_type(typed.translation(vector), typed.Transform)
    assert_type(typed.translation(1, scalar, 3), typed.Transform)
    rotation = assert_type(context.call(typed.rotation, quaternion), typed.Transform)
    assert_type(context.call(typed.rotation, vector, scalar), typed.Transform)
    assert_type(typed.rotation(quaternion), typed.Transform)
    assert_type(typed.rotation(vector, scalar), typed.Transform)
    assert_type(typed.rotate(vector, scalar), typed.Transform)
    scaling = assert_type(context.call(typed.scale, scalar), typed.Transform)
    assert_type(context.call(typed.scale, scalar, center=point), typed.Transform)
    assert_type(typed.scale(scalar, center=point), typed.Transform)
    reflection = assert_type(context.call(typed.mirror, vector), typed.Transform)
    assert_type(context.call(typed.mirror, vector, origin=point), typed.Transform)
    assert_type(typed.mirror(vector, origin=point), typed.Transform)
    assert_type(typed.short_rotate(vector, (1, 0, 0)), typed.Transform)

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

    affine_identity = assert_type(
        context.call(
            typed.identity_affine_transform,
        ),
        typed.AffineTransform,
    )
    assert_type(typed.identity_affine_transform(), typed.AffineTransform)
    affine = assert_type(
        context.call(
            typed.affine,
            (
                (1, scalar, 0, 3),
                (0, 2, 0, 4),
                (0, 0, 3, 5),
            ),
        ),
        typed.AffineTransform,
    )
    assert_type(
        typed.AffineTransform(
            ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            context=context,
        ),
        typed.AffineTransform,
    )
    assert_type(
        typed.GeneralTransformation.scaleXYZ(2, 3, 4, context=context),
        typed.AffineTransform,
    )
    assert_type(context.call(typed.scaleX, scalar), typed.AffineTransform)
    assert_type(context.call(typed.scaleY, scalar, center=point), typed.AffineTransform)
    assert_type(context.call(typed.scaleZ, scalar), typed.AffineTransform)
    assert_type(context.call(typed.scaleXYZ, 2, 3, scalar), typed.AffineTransform)
    assert_type(typed.scaleXYZ(2, 3, scalar), typed.AffineTransform)
    assert_type(translation.to_affine(), typed.AffineTransform)
    assert_type(
        typed.AffineTransform.from_transform(translation),
        typed.AffineTransform,
    )
    assert_type(affine_identity * affine, typed.AffineTransform)
    assert_type(affine * translation, typed.AffineTransform)
    assert_type(translation * affine, typed.AffineTransform)
    assert_type(affine.then(translation), typed.AffineTransform)
    assert_type(translation.then(affine), typed.AffineTransform)
    assert_type(affine.inverse(), typed.AffineTransform)
    assert_type(affine.translation, typed.Vector3)
    assert_type(affine.determinant, typed.Scalar)
    assert_type(affine.apply(point), typed.Point3)
    assert_type(affine.apply(vector), typed.Vector3)
    assert_type(affine(point), typed.Point3)
    assert_type(affine(vector), typed.Vector3)
    assert_type(affine.matrix(), Matrix4x4)

    shape = context.call(typed.box, 1)
    assert_type(shape.transform(translation), typed.Solid)
    assert_type(shape.transform(affine), typed.Solid)
    assert_type(shape.scaleX(scalar), typed.Solid)
    assert_type(shape.scaleY(scalar), typed.Solid)
    assert_type(shape.scaleZ(scalar), typed.Solid)
    assert_type(shape.scaleXYZ(2, 3, scalar), typed.Solid)
