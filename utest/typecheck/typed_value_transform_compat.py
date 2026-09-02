"""Static contract for the legacy value and transform compatibility slice."""

from typing_extensions import assert_type

from zencad import geom as typed


def value_transform_compatibility(context: typed.Context) -> None:
    scalar = context.call(typed.scalar, 1)
    point = assert_type(context.call(typed.point3, 1, scalar), typed.Point3)
    vector = assert_type(context.call(typed.vector3, (1, 2, 3)), typed.Vector3)
    quaternion = assert_type(
        context.call(typed.quaternion, 0, 0, 0, 1),
        typed.Quaternion,
    )
    assert_type(
        [context.call(typed.point3, value) for value in ((1, 2, 3), point)],
        list[typed.Point3],
    )
    assert_type(
        [
            [context.call(typed.point3, value) for value in row]
            for row in (((1, 2, 3),),)
        ],
        list[list[typed.Point3]],
    )
    assert_type(
        [context.call(typed.vector3, value) for value in ((1, 2, 3), vector)],
        list[typed.Vector3],
    )
    assert_type(typed.points(((1, 2, 3), point)), list[typed.Point3])
    assert_type(typed.points2((((1, 2, 3),),)), list[list[typed.Point3]])
    assert_type(typed.vectors(((1, 2, 3), vector)), list[typed.Vector3])

    assert_type(point.to_vector3(), typed.Vector3)
    assert_type(vector.to_point3(), typed.Point3)
    assert_type(point.cross(vector), typed.Vector3)
    assert_type(point.distance(point), typed.Scalar)
    assert_type(vector.angle(vector), typed.Scalar)
    assert_type(vector.normalize(), typed.Vector3)

    transform = assert_type(context.call(typed.move, vector), typed.Transform)
    assert_type(context.call(typed.translate, 1, scalar, 3), typed.Transform)
    assert_type(context.call(typed.right, scalar), typed.Transform)
    assert_type(context.call(typed.forw, scalar), typed.Transform)
    assert_type(context.call(typed.up, scalar), typed.Transform)
    assert_type(context.call(typed.rotate, vector, scalar), typed.Transform)
    assert_type(context.call(typed.rotate, vector), typed.Transform)
    assert_type(quaternion.to_transform(), typed.Transform)
    assert_type(context.call(typed.rotateX, scalar), typed.Transform)
    assert_type(
        context.call(
            typed.mirrorXY,
        ),
        typed.Transform,
    )
    assert_type(
        context.call(
            typed.mirrorX,
        ),
        typed.Transform,
    )
    assert_type(context.call(typed.mirrorO, point), typed.Transform)

    assert_type(transform.transform_point(point), typed.Point3)
    assert_type(transform.transform_vector(vector), typed.Vector3)
    assert_type(transform.inverse_transform_point(point), typed.Point3)
    assert_type(transform.inverse_transform_vector(vector), typed.Vector3)
    assert_type(transform.rotation_quat(), typed.Quaternion)
    assert_type(transform.rotation_euler(), typed.Vector3)
    assert_type(transform.rotation_axis_angle(), tuple[typed.Vector3, typed.Scalar])

    solid = context.call(typed.box, 1)
    assert_type(solid.move(vector), typed.Solid)
    assert_type(solid.mov(1, 2, scalar), typed.Solid)
    assert_type(solid.right(scalar).forw(2).up(3), typed.Solid)
    assert_type(solid.rotate(vector, scalar), typed.Solid)
    assert_type(solid.rotZ(scalar), typed.Solid)
    assert_type(solid.scale(scalar, point), typed.Solid)
    assert_type(solid.mirrorXY(), typed.Solid)

    multi = assert_type(
        typed.MultiTransform(
            (context.call(typed.nulltrans), transform),
            context=context,
            array=True,
        ),
        typed.MultiTransform,
    )
    assert_type(multi.items(solid), list[typed.Solid])
    assert_type(multi.fused(solid), typed.Shape)
    assert_type(multi(solid), typed.Shape | list[typed.Solid])
    assert_type(
        typed.MultiTransform((transform,), context=context),
        typed.MultiTransform,
    )
    assert_type(context.call(typed.short_rotate, vector, (0, 1, 0)), typed.Transform)
