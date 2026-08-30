"""Pure resolved operations for Scalar, Point, and Vector handles."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct


def _key(tag: bytes, *coordinates: float) -> bytes:
    return tag + struct.pack(">" + "d" * len(coordinates), *coordinates)


@dataclass(frozen=True)
class Point2Value:
    x: float
    y: float

    def __evalcache_key__(self) -> bytes:
        return _key(b"point2-v1\x00", self.x, self.y)


@dataclass(frozen=True)
class Vector2Value:
    x: float
    y: float

    def __evalcache_key__(self) -> bytes:
        return _key(b"vector2-v1\x00", self.x, self.y)


@dataclass(frozen=True)
class Point3Value:
    x: float
    y: float
    z: float

    def __evalcache_key__(self) -> bytes:
        return _key(b"point3-v1\x00", self.x, self.y, self.z)


@dataclass(frozen=True)
class Vector3Value:
    x: float
    y: float
    z: float

    def __evalcache_key__(self) -> bytes:
        return _key(b"vector3-v1\x00", self.x, self.y, self.z)


def scalar_add(left: float, right: float) -> float:
    return left + right


def scalar_subtract(left: float, right: float) -> float:
    return left - right


def scalar_multiply(left: float, right: float) -> float:
    return left * right


def scalar_divide(left: float, right: float) -> float:
    return left / right


def scalar_floor_divide(left: float, right: float) -> float:
    return float(left // right)


def scalar_modulo(left: float, right: float) -> float:
    return left % right


def scalar_power(left: float, right: float) -> float:
    return float(left**right)


def scalar_negate(value: float) -> float:
    return -value


def scalar_absolute(value: float) -> float:
    return abs(value)


def scalar_sin(value: float) -> float:
    return math.sin(value)


def scalar_cos(value: float) -> float:
    return math.cos(value)


def scalar_tan(value: float) -> float:
    return math.tan(value)


def scalar_asin(value: float) -> float:
    return math.asin(value)


def scalar_acos(value: float) -> float:
    return math.acos(value)


def scalar_atan(value: float) -> float:
    return math.atan(value)


def scalar_sqrt(value: float) -> float:
    return math.sqrt(value)


def scalar_exp(value: float) -> float:
    return math.exp(value)


def scalar_log(value: float) -> float:
    return math.log(value)


def scalar_atan2(y: float, x: float) -> float:
    return math.atan2(y, x)


def point2(x: float, y: float) -> Point2Value:
    return Point2Value(x, y)


def vector2(x: float, y: float) -> Vector2Value:
    return Vector2Value(x, y)


def point3(x: float, y: float, z: float) -> Point3Value:
    return Point3Value(x, y, z)


def vector3(x: float, y: float, z: float) -> Vector3Value:
    return Vector3Value(x, y, z)


def point2_coordinate(value: Point2Value, axis: int) -> float:
    return (value.x, value.y)[axis]


def vector2_coordinate(value: Vector2Value, axis: int) -> float:
    return (value.x, value.y)[axis]


def point3_coordinate(value: Point3Value, axis: int) -> float:
    return (value.x, value.y, value.z)[axis]


def vector3_coordinate(value: Vector3Value, axis: int) -> float:
    return (value.x, value.y, value.z)[axis]


def point2_add_vector(left: Point2Value, right: Vector2Value) -> Point2Value:
    return Point2Value(left.x + right.x, left.y + right.y)


def point2_subtract_vector(left: Point2Value, right: Vector2Value) -> Point2Value:
    return Point2Value(left.x - right.x, left.y - right.y)


def point2_subtract_point(left: Point2Value, right: Point2Value) -> Vector2Value:
    return Vector2Value(left.x - right.x, left.y - right.y)


def point2_distance(left: Point2Value, right: Point2Value) -> float:
    return math.hypot(left.x - right.x, left.y - right.y)


def vector2_add(left: Vector2Value, right: Vector2Value) -> Vector2Value:
    return Vector2Value(left.x + right.x, left.y + right.y)


def vector2_subtract(left: Vector2Value, right: Vector2Value) -> Vector2Value:
    return Vector2Value(left.x - right.x, left.y - right.y)


def vector2_add_point(left: Vector2Value, right: Point2Value) -> Point2Value:
    return Point2Value(left.x + right.x, left.y + right.y)


def vector2_scale(value: Vector2Value, factor: float) -> Vector2Value:
    return Vector2Value(value.x * factor, value.y * factor)


def vector2_divide(value: Vector2Value, divisor: float) -> Vector2Value:
    return Vector2Value(value.x / divisor, value.y / divisor)


def vector2_negate(value: Vector2Value) -> Vector2Value:
    return Vector2Value(-value.x, -value.y)


def vector2_dot(left: Vector2Value, right: Vector2Value) -> float:
    return left.x * right.x + left.y * right.y


def vector2_cross(left: Vector2Value, right: Vector2Value) -> float:
    return left.x * right.y - left.y * right.x


def vector2_length(value: Vector2Value) -> float:
    return math.hypot(value.x, value.y)


def vector2_normalized(value: Vector2Value) -> Vector2Value:
    length = vector2_length(value)
    if length == 0:
        raise ValueError("cannot normalize a zero-length vector")
    return vector2_divide(value, length)


def point3_add_vector(left: Point3Value, right: Vector3Value) -> Point3Value:
    return Point3Value(left.x + right.x, left.y + right.y, left.z + right.z)


def point3_subtract_vector(left: Point3Value, right: Vector3Value) -> Point3Value:
    return Point3Value(left.x - right.x, left.y - right.y, left.z - right.z)


def point3_subtract_point(left: Point3Value, right: Point3Value) -> Vector3Value:
    return Vector3Value(left.x - right.x, left.y - right.y, left.z - right.z)


def point3_distance(left: Point3Value, right: Point3Value) -> float:
    return math.sqrt(
        (left.x - right.x) ** 2 + (left.y - right.y) ** 2 + (left.z - right.z) ** 2
    )


def vector3_add(left: Vector3Value, right: Vector3Value) -> Vector3Value:
    return Vector3Value(left.x + right.x, left.y + right.y, left.z + right.z)


def vector3_subtract(left: Vector3Value, right: Vector3Value) -> Vector3Value:
    return Vector3Value(left.x - right.x, left.y - right.y, left.z - right.z)


def vector3_add_point(left: Vector3Value, right: Point3Value) -> Point3Value:
    return Point3Value(left.x + right.x, left.y + right.y, left.z + right.z)


def vector3_scale(value: Vector3Value, factor: float) -> Vector3Value:
    return Vector3Value(value.x * factor, value.y * factor, value.z * factor)


def vector3_divide(value: Vector3Value, divisor: float) -> Vector3Value:
    return Vector3Value(value.x / divisor, value.y / divisor, value.z / divisor)


def vector3_negate(value: Vector3Value) -> Vector3Value:
    return Vector3Value(-value.x, -value.y, -value.z)


def vector3_dot(left: Vector3Value, right: Vector3Value) -> float:
    return left.x * right.x + left.y * right.y + left.z * right.z


def vector3_cross(left: Vector3Value, right: Vector3Value) -> Vector3Value:
    return Vector3Value(
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    )


def vector3_length(value: Vector3Value) -> float:
    return math.sqrt(value.x**2 + value.y**2 + value.z**2)


def vector3_normalized(value: Vector3Value) -> Vector3Value:
    length = vector3_length(value)
    if length == 0:
        raise ValueError("cannot normalize a zero-length vector")
    return vector3_divide(value, length)
