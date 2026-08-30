"""Resolved immutable operations for typed rotations and transforms.

The value objects in this module are deliberately independent from mutable OCP
objects. OCP conversion is an explicit boundary implemented at the bottom of
the module; expression construction remains the responsibility of ``Runtime``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
import sys

from OCP.gp import gp_Quaternion, gp_Trsf, gp_Vec

from ._value_operations import Point3Value, Vector3Value


Matrix3x4 = tuple[
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]


@dataclass(frozen=True)
class QuaternionValue:
    """Canonical unit quaternion in ``(x, y, z, w)`` order."""

    x: float
    y: float
    z: float
    w: float

    def __evalcache_key__(self) -> bytes:
        return b"quaternion-v1\x00" + struct.pack(
            ">dddd", self.x, self.y, self.z, self.w
        )


@dataclass(frozen=True)
class TransformValue:
    """A similarity transform ``p -> scale * rotation(p) + translation``.

    Signed uniform scale covers every ``gp_Trsf`` transformation, including
    mirrors, without admitting shear or non-uniform scale. Those belong to a
    future, explicitly separate affine-transform type.
    """

    scale: float
    rotation: QuaternionValue
    translation: Vector3Value

    def __post_init__(self) -> None:
        if not math.isfinite(self.scale) or abs(self.scale) <= sys.float_info.min:
            raise ValueError("transform scale magnitude must exceed the OCP minimum")
        if not all(
            math.isfinite(component)
            for component in (
                self.translation.x,
                self.translation.y,
                self.translation.z,
            )
        ):
            raise ValueError("transform translation must be finite")

    def __evalcache_key__(self) -> bytes:
        return b"transform-v1\x00" + struct.pack(
            ">8d",
            self.scale,
            self.rotation.x,
            self.rotation.y,
            self.rotation.z,
            self.rotation.w,
            self.translation.x,
            self.translation.y,
            self.translation.z,
        )


_IDENTITY_QUATERNION = QuaternionValue(0.0, 0.0, 0.0, 1.0)
_ZERO_VECTOR = Vector3Value(0.0, 0.0, 0.0)
_IDENTITY_TRANSFORM = TransformValue(
    1.0,
    _IDENTITY_QUATERNION,
    _ZERO_VECTOR,
)


def _clean_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


def _translation_value(x: float, y: float, z: float) -> Vector3Value:
    if not all(math.isfinite(component) for component in (x, y, z)):
        raise ValueError("transform translation must be finite")
    return Vector3Value(_clean_zero(x), _clean_zero(y), _clean_zero(z))


def quaternion(x: float, y: float, z: float, w: float) -> QuaternionValue:
    """Build a canonical unit rotation quaternion."""
    if not all(math.isfinite(component) for component in (x, y, z, w)):
        raise ValueError("quaternion components must be finite")
    length = math.hypot(x, y, z, w)
    if length == 0.0:
        raise ValueError("a rotation quaternion cannot be zero")
    if length == 1.0:
        values = (x, y, z, w)
    else:
        values = (x / length, y / length, z / length, w / length)
    # q and -q describe the same rotation. Canonicalizing their sign gives
    # equivalent rotations one deterministic value and cache identity.
    for component in (values[3], values[0], values[1], values[2]):
        if component != 0.0:
            if component < 0.0:
                values = tuple(-value for value in values)
            break
    values = tuple(_clean_zero(value) for value in values)
    return QuaternionValue(*values)


def quaternion_coordinate(value: QuaternionValue, axis: int) -> float:
    return (value.x, value.y, value.z, value.w)[axis]


def quaternion_axis_angle(axis: Vector3Value, angle: float) -> QuaternionValue:
    if not math.isfinite(angle):
        raise ValueError("a rotation angle must be finite")
    if not all(math.isfinite(component) for component in (axis.x, axis.y, axis.z)):
        raise ValueError("a rotation axis must be finite")
    length = math.hypot(axis.x, axis.y, axis.z)
    if length == 0.0:
        raise ValueError("a rotation axis cannot be zero-length")
    half_angle = angle / 2.0
    sine = math.sin(half_angle)
    return quaternion(
        (axis.x / length) * sine,
        (axis.y / length) * sine,
        (axis.z / length) * sine,
        math.cos(half_angle),
    )


def quaternion_compose(
    outer: QuaternionValue, inner: QuaternionValue
) -> QuaternionValue:
    """Compose rotations so ``outer * inner`` applies ``inner`` first."""
    if outer == _IDENTITY_QUATERNION:
        return inner
    if inner == _IDENTITY_QUATERNION:
        return outer
    return quaternion(
        outer.w * inner.x + outer.x * inner.w + outer.y * inner.z - outer.z * inner.y,
        outer.w * inner.y - outer.x * inner.z + outer.y * inner.w + outer.z * inner.x,
        outer.w * inner.z + outer.x * inner.y - outer.y * inner.x + outer.z * inner.w,
        outer.w * inner.w - outer.x * inner.x - outer.y * inner.y - outer.z * inner.z,
    )


def quaternion_inverse(value: QuaternionValue) -> QuaternionValue:
    if value == _IDENTITY_QUATERNION:
        return value
    return quaternion(-value.x, -value.y, -value.z, value.w)


def quaternion_norm(value: QuaternionValue) -> float:
    return math.hypot(value.x, value.y, value.z, value.w)


def _rotation_matrix(
    value: QuaternionValue,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]:
    x, y, z, w = value.x, value.y, value.z, value.w
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        1.0 - 2.0 * (yy + zz),
        2.0 * (xy - wz),
        2.0 * (xz + wy),
        2.0 * (xy + wz),
        1.0 - 2.0 * (xx + zz),
        2.0 * (yz - wx),
        2.0 * (xz - wy),
        2.0 * (yz + wx),
        1.0 - 2.0 * (xx + yy),
    )


def quaternion_rotate_vector(
    rotation: QuaternionValue, vector: Vector3Value
) -> Vector3Value:
    matrix = _rotation_matrix(rotation)
    return Vector3Value(
        matrix[0] * vector.x + matrix[1] * vector.y + matrix[2] * vector.z,
        matrix[3] * vector.x + matrix[4] * vector.y + matrix[5] * vector.z,
        matrix[6] * vector.x + matrix[7] * vector.y + matrix[8] * vector.z,
    )


def identity_transform() -> TransformValue:
    return _IDENTITY_TRANSFORM


def translation_transform(vector: Vector3Value) -> TransformValue:
    return TransformValue(
        1.0,
        _IDENTITY_QUATERNION,
        _translation_value(vector.x, vector.y, vector.z),
    )


def rotation_transform(rotation: QuaternionValue) -> TransformValue:
    if rotation == _IDENTITY_QUATERNION:
        return _IDENTITY_TRANSFORM
    return TransformValue(1.0, rotation, _ZERO_VECTOR)


def scale_transform(factor: float, center: Point3Value) -> TransformValue:
    if not math.isfinite(factor) or abs(factor) <= sys.float_info.min:
        raise ValueError("typed transform scale magnitude must exceed the OCP minimum")
    if not all(
        math.isfinite(component) for component in (center.x, center.y, center.z)
    ):
        raise ValueError("a scale center must be finite")
    offset = 1.0 - factor
    return TransformValue(
        factor,
        _IDENTITY_QUATERNION,
        _translation_value(
            offset * center.x,
            offset * center.y,
            offset * center.z,
        ),
    )


def mirror_transform(normal: Vector3Value, origin: Point3Value) -> TransformValue:
    if not all(
        math.isfinite(component) for component in (normal.x, normal.y, normal.z)
    ):
        raise ValueError("a mirror plane normal must be finite")
    if not all(
        math.isfinite(component) for component in (origin.x, origin.y, origin.z)
    ):
        raise ValueError("a mirror plane origin must be finite")
    length = math.hypot(normal.x, normal.y, normal.z)
    if length == 0.0:
        raise ValueError("a mirror plane normal cannot be zero-length")
    x, y, z = normal.x / length, normal.y / length, normal.z / length
    distance = x * origin.x + y * origin.y + z * origin.z
    # Plane reflection A = I - 2nn^T equals signed scale -1 followed by
    # a pi rotation around n: A = -R_pi(n).
    rotation = quaternion(x, y, z, 0.0)
    return TransformValue(
        -1.0,
        rotation,
        _translation_value(
            2.0 * distance * x,
            2.0 * distance * y,
            2.0 * distance * z,
        ),
    )


def transform_compose(outer: TransformValue, inner: TransformValue) -> TransformValue:
    """Compose transforms so ``outer * inner`` applies ``inner`` first."""
    if outer == _IDENTITY_TRANSFORM:
        return inner
    if inner == _IDENTITY_TRANSFORM:
        return outer
    rotated_translation = quaternion_rotate_vector(outer.rotation, inner.translation)
    scale = outer.scale * inner.scale
    translation = _translation_value(
        outer.translation.x + outer.scale * rotated_translation.x,
        outer.translation.y + outer.scale * rotated_translation.y,
        outer.translation.z + outer.scale * rotated_translation.z,
    )
    return TransformValue(
        scale,
        quaternion_compose(outer.rotation, inner.rotation),
        translation,
    )


def transform_inverse(value: TransformValue) -> TransformValue:
    if value == _IDENTITY_TRANSFORM:
        return value
    inverse_scale = 1.0 / value.scale
    if not math.isfinite(inverse_scale) or abs(inverse_scale) <= sys.float_info.min:
        raise ValueError("inverse scale is outside the OCP transform range")
    inverse_rotation = quaternion_inverse(value.rotation)
    rotated_translation = quaternion_rotate_vector(inverse_rotation, value.translation)
    return TransformValue(
        inverse_scale,
        inverse_rotation,
        _translation_value(
            -inverse_scale * rotated_translation.x,
            -inverse_scale * rotated_translation.y,
            -inverse_scale * rotated_translation.z,
        ),
    )


def transform_point(transform: TransformValue, point: Point3Value) -> Point3Value:
    rotated = quaternion_rotate_vector(
        transform.rotation, Vector3Value(point.x, point.y, point.z)
    )
    return Point3Value(
        transform.scale * rotated.x + transform.translation.x,
        transform.scale * rotated.y + transform.translation.y,
        transform.scale * rotated.z + transform.translation.z,
    )


def transform_vector(transform: TransformValue, vector: Vector3Value) -> Vector3Value:
    rotated = quaternion_rotate_vector(transform.rotation, vector)
    return Vector3Value(
        transform.scale * rotated.x,
        transform.scale * rotated.y,
        transform.scale * rotated.z,
    )


def transform_matrix(value: TransformValue) -> Matrix3x4:
    rotation = _rotation_matrix(value.rotation)
    return (
        value.scale * rotation[0],
        value.scale * rotation[1],
        value.scale * rotation[2],
        value.translation.x,
        value.scale * rotation[3],
        value.scale * rotation[4],
        value.scale * rotation[5],
        value.translation.y,
        value.scale * rotation[6],
        value.scale * rotation[7],
        value.scale * rotation[8],
        value.translation.z,
    )


def transform_scale(value: TransformValue) -> float:
    return value.scale


def transform_rotation(value: TransformValue) -> QuaternionValue:
    return value.rotation


def transform_translation(value: TransformValue) -> Vector3Value:
    return value.translation


def transform_from_ocp(value: gp_Trsf) -> TransformValue:
    translation = value.TranslationPart()
    return TransformValue(
        float(value.ScaleFactor()),
        quaternion_from_ocp(value.GetRotation()),
        _translation_value(
            float(translation.X()),
            float(translation.Y()),
            float(translation.Z()),
        ),
    )


def transform_to_ocp(value: TransformValue) -> gp_Trsf:
    transform = gp_Trsf()
    # SetRotation resets other parts, so the order is intentional.
    transform.SetRotation(quaternion_to_ocp(value.rotation))
    transform.SetScaleFactor(value.scale)
    transform.SetTranslationPart(
        gp_Vec(
            value.translation.x,
            value.translation.y,
            value.translation.z,
        )
    )
    return transform


def quaternion_from_ocp(value: gp_Quaternion) -> QuaternionValue:
    return quaternion(value.X(), value.Y(), value.Z(), value.W())


def quaternion_to_ocp(value: QuaternionValue) -> gp_Quaternion:
    return gp_Quaternion(value.x, value.y, value.z, value.w)
