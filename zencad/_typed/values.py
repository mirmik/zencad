"""Typed Scalar, Point, and Vector handles with expression-aware algebra."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Callable, TypeVar, Union, cast, overload

import numpy
from OCP.gp import gp_Pnt, gp_Pnt2d, gp_Vec, gp_Vec2d
from evalcache.v2 import ResultSpec

from . import _value_operations as ops
from ._core import Handle, State, require_same_runtime

if TYPE_CHECKING:
    from .runtime import Runtime


Number = int | float
ScalarInput = Union[Number, "Scalar"]
ValueT = TypeVar("ValueT")


SCALAR_SPEC = ResultSpec.for_type(float, type_id="zencad.typed.Scalar.v1")
POINT2_SPEC = ResultSpec.for_type(ops.Point2Value, type_id="zencad.typed.Point2.v1")
VECTOR2_SPEC = ResultSpec.for_type(ops.Vector2Value, type_id="zencad.typed.Vector2.v1")
POINT3_SPEC = ResultSpec.for_type(ops.Point3Value, type_id="zencad.typed.Point3.v1")
VECTOR3_SPEC = ResultSpec.for_type(ops.Vector3Value, type_id="zencad.typed.Vector3.v1")


def _number(value: Number) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("expected int or float")
    return float(value)


def _scalar_state(runtime: Runtime, value: ScalarInput) -> State[float]:
    if isinstance(value, Scalar):
        require_same_runtime(runtime, value)
        return value._state
    return _number(value)


def _infer_runtime(
    explicit: Runtime | None, values: tuple[ScalarInput, ...]
) -> Runtime:
    runtimes = {value.runtime for value in values if isinstance(value, Scalar)}
    if explicit is not None:
        runtimes.add(explicit)
    if not runtimes:
        raise TypeError("literal value construction requires runtime=")
    if len(runtimes) != 1:
        raise ValueError("cannot mix handles from different typed runtimes")
    return next(iter(runtimes))


def _resolved_scalar(runtime: Runtime, value: ScalarInput) -> float:
    if isinstance(value, Scalar):
        require_same_runtime(runtime, value)
        return value.value()
    return _number(value)


class Scalar(Handle[float]):
    """Immutable numeric handle; Python conversions are materialization boundaries."""

    def __init__(self, value: Number, *, runtime: Runtime) -> None:
        self._bind(runtime, _number(value))

    @classmethod
    def _from_state(cls, runtime: Runtime, state: State[float]) -> Scalar:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    def value(self) -> float:
        return self._resolved()

    def __float__(self) -> float:
        return self.value()

    def __int__(self) -> int:
        return int(self.value())

    def __bool__(self) -> bool:
        return bool(self.value())

    def _binary(
        self,
        other: ScalarInput,
        operation: Callable[[float, float], float],
        operation_id: str,
    ) -> Scalar:
        state = self.runtime._value_state(
            operation,
            result=SCALAR_SPEC,
            args=(self._state, _scalar_state(self.runtime, other)),
            operation_id=operation_id,
        )
        return Scalar._from_state(self.runtime, state)

    def _reflected_binary(
        self,
        other: ScalarInput,
        operation: Callable[[float, float], float],
        operation_id: str,
    ) -> Scalar:
        state = self.runtime._value_state(
            operation,
            result=SCALAR_SPEC,
            args=(_scalar_state(self.runtime, other), self._state),
            operation_id=operation_id,
        )
        return Scalar._from_state(self.runtime, state)

    def _unary(self, operation: Callable[[float], float], operation_id: str) -> Scalar:
        state = self.runtime._value_state(
            operation,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id=operation_id,
        )
        return Scalar._from_state(self.runtime, state)

    def __add__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_add, "zencad.typed.scalar.add")

    def __radd__(self, other: ScalarInput) -> Scalar:
        return self.__add__(other)

    def __sub__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_subtract, "zencad.typed.scalar.subtract")

    def __rsub__(self, other: ScalarInput) -> Scalar:
        return self._reflected_binary(
            other, ops.scalar_subtract, "zencad.typed.scalar.subtract"
        )

    @overload
    def __mul__(self, other: ScalarInput) -> Scalar: ...

    @overload
    def __mul__(self, other: Vector2) -> Vector2: ...

    @overload
    def __mul__(self, other: Vector3) -> Vector3: ...

    def __mul__(self, other: object) -> Scalar | Vector2 | Vector3:
        if isinstance(other, (Vector2, Vector3)):
            return other * self
        return self._binary(
            cast(ScalarInput, other),
            ops.scalar_multiply,
            "zencad.typed.scalar.multiply",
        )

    def __rmul__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_multiply, "zencad.typed.scalar.multiply")

    def __truediv__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_divide, "zencad.typed.scalar.divide")

    def __rtruediv__(self, other: ScalarInput) -> Scalar:
        return self._reflected_binary(
            other, ops.scalar_divide, "zencad.typed.scalar.divide"
        )

    def __floordiv__(self, other: ScalarInput) -> Scalar:
        return self._binary(
            other, ops.scalar_floor_divide, "zencad.typed.scalar.floor_divide"
        )

    def __rfloordiv__(self, other: ScalarInput) -> Scalar:
        return self._reflected_binary(
            other, ops.scalar_floor_divide, "zencad.typed.scalar.floor_divide"
        )

    def __mod__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_modulo, "zencad.typed.scalar.modulo")

    def __rmod__(self, other: ScalarInput) -> Scalar:
        return self._reflected_binary(
            other, ops.scalar_modulo, "zencad.typed.scalar.modulo"
        )

    def __pow__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_power, "zencad.typed.scalar.power")

    def __rpow__(self, other: ScalarInput) -> Scalar:
        return self._reflected_binary(
            other, ops.scalar_power, "zencad.typed.scalar.power"
        )

    def __neg__(self) -> Scalar:
        return self._unary(ops.scalar_negate, "zencad.typed.scalar.negate")

    def __pos__(self) -> Scalar:
        return self

    def __abs__(self) -> Scalar:
        return self._unary(ops.scalar_absolute, "zencad.typed.scalar.absolute")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Scalar, int, float)) or isinstance(other, bool):
            return False
        return self.value() == _resolved_scalar(self.runtime, other)

    def __lt__(self, other: ScalarInput) -> bool:
        return self.value() < _resolved_scalar(self.runtime, other)

    def __le__(self, other: ScalarInput) -> bool:
        return self.value() <= _resolved_scalar(self.runtime, other)

    def __gt__(self, other: ScalarInput) -> bool:
        return self.value() > _resolved_scalar(self.runtime, other)

    def __ge__(self, other: ScalarInput) -> bool:
        return self.value() >= _resolved_scalar(self.runtime, other)


class _CoordinateHandle(Handle[ValueT]):
    def _coordinate(
        self,
        axis: int,
        operation: Callable[[ValueT, int], float],
        operation_id: str,
    ) -> Scalar:
        state = self.runtime._value_state(
            operation,
            result=SCALAR_SPEC,
            args=(self._state, axis),
            operation_id=operation_id,
        )
        return Scalar._from_state(self.runtime, state)

    def to_numpy(self) -> numpy.ndarray:
        return numpy.asarray(tuple(self), dtype=float)


class Point2(_CoordinateHandle[ops.Point2Value]):
    @overload
    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput],
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput | tuple[ScalarInput, ScalarInput],
        y: ScalarInput | None = None,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        components = _components2(x, y)
        resolved_runtime = _infer_runtime(runtime, components)
        state = resolved_runtime._value_state(
            ops.point2,
            result=POINT2_SPEC,
            args=tuple(_scalar_state(resolved_runtime, item) for item in components),
            operation_id="zencad.typed.point2",
        )
        self._bind(resolved_runtime, state)

    @classmethod
    def _from_state(cls, runtime: Runtime, state: State[ops.Point2Value]) -> Point2:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @property
    def x(self) -> Scalar:
        return self._coordinate(
            0, ops.point2_coordinate, "zencad.typed.point2.coordinate"
        )

    @property
    def y(self) -> Scalar:
        return self._coordinate(
            1, ops.point2_coordinate, "zencad.typed.point2.coordinate"
        )

    def value(self) -> tuple[float, float]:
        value = self._resolved()
        return (value.x, value.y)

    def __iter__(self) -> Iterator[float]:
        return iter(self.value())

    def __add__(self, other: Vector2) -> Point2:
        if not isinstance(other, Vector2):
            raise TypeError("Point2 can only be added to Vector2")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.point2_add_vector,
            result=POINT2_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point2.add_vector",
        )
        return Point2._from_state(self.runtime, state)

    @overload
    def __sub__(self, other: Point2) -> Vector2: ...

    @overload
    def __sub__(self, other: Vector2) -> Point2: ...

    def __sub__(self, other: Point2 | Vector2) -> Vector2 | Point2:
        if not isinstance(other, (Point2, Vector2)):
            raise TypeError("Point2 can only subtract Point2 or Vector2")
        require_same_runtime(self.runtime, other)
        if isinstance(other, Point2):
            state = self.runtime._value_state(
                ops.point2_subtract_point,
                result=VECTOR2_SPEC,
                args=(self._state, other._state),
                operation_id="zencad.typed.point2.subtract_point",
            )
            return Vector2._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.point2_subtract_vector,
            result=POINT2_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point2.subtract_vector",
        )
        return Point2._from_state(self.runtime, state)

    def distance_to(self, other: Point2) -> Scalar:
        if not isinstance(other, Point2):
            raise TypeError("Point2 distance requires Point2")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.point2_distance,
            result=SCALAR_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point2.distance",
        )
        return Scalar._from_state(self.runtime, state)

    def to_ocp(self) -> gp_Pnt2d:
        x, y = self.value()
        return gp_Pnt2d(x, y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point2):
            return False
        require_same_runtime(self.runtime, other)
        return self.value() == other.value()


class Vector2(_CoordinateHandle[ops.Vector2Value]):
    @overload
    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput],
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput | tuple[ScalarInput, ScalarInput],
        y: ScalarInput | None = None,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        components = _components2(x, y)
        resolved_runtime = _infer_runtime(runtime, components)
        state = resolved_runtime._value_state(
            ops.vector2,
            result=VECTOR2_SPEC,
            args=tuple(_scalar_state(resolved_runtime, item) for item in components),
            operation_id="zencad.typed.vector2",
        )
        self._bind(resolved_runtime, state)

    @classmethod
    def _from_state(cls, runtime: Runtime, state: State[ops.Vector2Value]) -> Vector2:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @property
    def x(self) -> Scalar:
        return self._coordinate(
            0, ops.vector2_coordinate, "zencad.typed.vector2.coordinate"
        )

    @property
    def y(self) -> Scalar:
        return self._coordinate(
            1, ops.vector2_coordinate, "zencad.typed.vector2.coordinate"
        )

    def value(self) -> tuple[float, float]:
        value = self._resolved()
        return (value.x, value.y)

    def __iter__(self) -> Iterator[float]:
        return iter(self.value())

    @overload
    def __add__(self, other: Vector2) -> Vector2: ...

    @overload
    def __add__(self, other: Point2) -> Point2: ...

    def __add__(self, other: Vector2 | Point2) -> Vector2 | Point2:
        if not isinstance(other, (Vector2, Point2)):
            raise TypeError("Vector2 can only be added to Vector2 or Point2")
        require_same_runtime(self.runtime, other)
        if isinstance(other, Point2):
            state = self.runtime._value_state(
                ops.vector2_add_point,
                result=POINT2_SPEC,
                args=(self._state, other._state),
                operation_id="zencad.typed.vector2.add_point",
            )
            return Point2._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.vector2_add,
            result=VECTOR2_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector2.add",
        )
        return Vector2._from_state(self.runtime, state)

    def __sub__(self, other: Vector2) -> Vector2:
        if not isinstance(other, Vector2):
            raise TypeError("Vector2 can only subtract Vector2")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector2_subtract,
            result=VECTOR2_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector2.subtract",
        )
        return Vector2._from_state(self.runtime, state)

    def __mul__(self, factor: ScalarInput) -> Vector2:
        state = self.runtime._value_state(
            ops.vector2_scale,
            result=VECTOR2_SPEC,
            args=(self._state, _scalar_state(self.runtime, factor)),
            operation_id="zencad.typed.vector2.scale",
        )
        return Vector2._from_state(self.runtime, state)

    def __rmul__(self, factor: ScalarInput) -> Vector2:
        return self * factor

    def __truediv__(self, divisor: ScalarInput) -> Vector2:
        state = self.runtime._value_state(
            ops.vector2_divide,
            result=VECTOR2_SPEC,
            args=(self._state, _scalar_state(self.runtime, divisor)),
            operation_id="zencad.typed.vector2.divide",
        )
        return Vector2._from_state(self.runtime, state)

    def __neg__(self) -> Vector2:
        state = self.runtime._value_state(
            ops.vector2_negate,
            result=VECTOR2_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector2.negate",
        )
        return Vector2._from_state(self.runtime, state)

    def dot(self, other: Vector2) -> Scalar:
        if not isinstance(other, Vector2):
            raise TypeError("Vector2 dot product requires Vector2")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector2_dot,
            result=SCALAR_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector2.dot",
        )
        return Scalar._from_state(self.runtime, state)

    def cross(self, other: Vector2) -> Scalar:
        if not isinstance(other, Vector2):
            raise TypeError("Vector2 cross product requires Vector2")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector2_cross,
            result=SCALAR_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector2.cross",
        )
        return Scalar._from_state(self.runtime, state)

    def length(self) -> Scalar:
        state = self.runtime._value_state(
            ops.vector2_length,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector2.length",
        )
        return Scalar._from_state(self.runtime, state)

    def normalized(self) -> Vector2:
        state = self.runtime._value_state(
            ops.vector2_normalized,
            result=VECTOR2_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector2.normalized",
        )
        return Vector2._from_state(self.runtime, state)

    def to_ocp(self) -> gp_Vec2d:
        x, y = self.value()
        return gp_Vec2d(x, y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return False
        require_same_runtime(self.runtime, other)
        return self.value() == other.value()


class Point3(_CoordinateHandle[ops.Point3Value]):
    @overload
    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput, ScalarInput],
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput | tuple[ScalarInput, ScalarInput, ScalarInput],
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        components = _components3(x, y, z)
        resolved_runtime = _infer_runtime(runtime, components)
        state = resolved_runtime._value_state(
            ops.point3,
            result=POINT3_SPEC,
            args=tuple(_scalar_state(resolved_runtime, item) for item in components),
            operation_id="zencad.typed.point3",
        )
        self._bind(resolved_runtime, state)

    @classmethod
    def _from_state(cls, runtime: Runtime, state: State[ops.Point3Value]) -> Point3:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @property
    def x(self) -> Scalar:
        return self._coordinate(
            0, ops.point3_coordinate, "zencad.typed.point3.coordinate"
        )

    @property
    def y(self) -> Scalar:
        return self._coordinate(
            1, ops.point3_coordinate, "zencad.typed.point3.coordinate"
        )

    @property
    def z(self) -> Scalar:
        return self._coordinate(
            2, ops.point3_coordinate, "zencad.typed.point3.coordinate"
        )

    def value(self) -> tuple[float, float, float]:
        value = self._resolved()
        return (value.x, value.y, value.z)

    def __iter__(self) -> Iterator[float]:
        return iter(self.value())

    def __add__(self, other: Vector3) -> Point3:
        if not isinstance(other, Vector3):
            raise TypeError("Point3 can only be added to Vector3")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.point3_add_vector,
            result=POINT3_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point3.add_vector",
        )
        return Point3._from_state(self.runtime, state)

    @overload
    def __sub__(self, other: Point3) -> Vector3: ...

    @overload
    def __sub__(self, other: Vector3) -> Point3: ...

    def __sub__(self, other: Point3 | Vector3) -> Vector3 | Point3:
        if not isinstance(other, (Point3, Vector3)):
            raise TypeError("Point3 can only subtract Point3 or Vector3")
        require_same_runtime(self.runtime, other)
        if isinstance(other, Point3):
            state = self.runtime._value_state(
                ops.point3_subtract_point,
                result=VECTOR3_SPEC,
                args=(self._state, other._state),
                operation_id="zencad.typed.point3.subtract_point",
            )
            return Vector3._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.point3_subtract_vector,
            result=POINT3_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point3.subtract_vector",
        )
        return Point3._from_state(self.runtime, state)

    def distance_to(self, other: Point3) -> Scalar:
        if not isinstance(other, Point3):
            raise TypeError("Point3 distance requires Point3")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.point3_distance,
            result=SCALAR_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.point3.distance",
        )
        return Scalar._from_state(self.runtime, state)

    def to_ocp(self) -> gp_Pnt:
        x, y, z = self.value()
        return gp_Pnt(x, y, z)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point3):
            return False
        require_same_runtime(self.runtime, other)
        return self.value() == other.value()


class Vector3(_CoordinateHandle[ops.Vector3Value]):
    @overload
    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput, ScalarInput],
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput | tuple[ScalarInput, ScalarInput, ScalarInput],
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        components = _components3(x, y, z)
        resolved_runtime = _infer_runtime(runtime, components)
        state = resolved_runtime._value_state(
            ops.vector3,
            result=VECTOR3_SPEC,
            args=tuple(_scalar_state(resolved_runtime, item) for item in components),
            operation_id="zencad.typed.vector3",
        )
        self._bind(resolved_runtime, state)

    @classmethod
    def _from_state(cls, runtime: Runtime, state: State[ops.Vector3Value]) -> Vector3:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @property
    def x(self) -> Scalar:
        return self._coordinate(
            0, ops.vector3_coordinate, "zencad.typed.vector3.coordinate"
        )

    @property
    def y(self) -> Scalar:
        return self._coordinate(
            1, ops.vector3_coordinate, "zencad.typed.vector3.coordinate"
        )

    @property
    def z(self) -> Scalar:
        return self._coordinate(
            2, ops.vector3_coordinate, "zencad.typed.vector3.coordinate"
        )

    def value(self) -> tuple[float, float, float]:
        value = self._resolved()
        return (value.x, value.y, value.z)

    def __iter__(self) -> Iterator[float]:
        return iter(self.value())

    @overload
    def __add__(self, other: Vector3) -> Vector3: ...

    @overload
    def __add__(self, other: Point3) -> Point3: ...

    def __add__(self, other: Vector3 | Point3) -> Vector3 | Point3:
        if not isinstance(other, (Vector3, Point3)):
            raise TypeError("Vector3 can only be added to Vector3 or Point3")
        require_same_runtime(self.runtime, other)
        if isinstance(other, Point3):
            state = self.runtime._value_state(
                ops.vector3_add_point,
                result=POINT3_SPEC,
                args=(self._state, other._state),
                operation_id="zencad.typed.vector3.add_point",
            )
            return Point3._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.vector3_add,
            result=VECTOR3_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector3.add",
        )
        return Vector3._from_state(self.runtime, state)

    def __sub__(self, other: Vector3) -> Vector3:
        if not isinstance(other, Vector3):
            raise TypeError("Vector3 can only subtract Vector3")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector3_subtract,
            result=VECTOR3_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector3.subtract",
        )
        return Vector3._from_state(self.runtime, state)

    def __mul__(self, factor: ScalarInput) -> Vector3:
        state = self.runtime._value_state(
            ops.vector3_scale,
            result=VECTOR3_SPEC,
            args=(self._state, _scalar_state(self.runtime, factor)),
            operation_id="zencad.typed.vector3.scale",
        )
        return Vector3._from_state(self.runtime, state)

    def __rmul__(self, factor: ScalarInput) -> Vector3:
        return self * factor

    def __truediv__(self, divisor: ScalarInput) -> Vector3:
        state = self.runtime._value_state(
            ops.vector3_divide,
            result=VECTOR3_SPEC,
            args=(self._state, _scalar_state(self.runtime, divisor)),
            operation_id="zencad.typed.vector3.divide",
        )
        return Vector3._from_state(self.runtime, state)

    def __neg__(self) -> Vector3:
        state = self.runtime._value_state(
            ops.vector3_negate,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector3.negate",
        )
        return Vector3._from_state(self.runtime, state)

    def dot(self, other: Vector3) -> Scalar:
        if not isinstance(other, Vector3):
            raise TypeError("Vector3 dot product requires Vector3")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector3_dot,
            result=SCALAR_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector3.dot",
        )
        return Scalar._from_state(self.runtime, state)

    def cross(self, other: Vector3) -> Vector3:
        if not isinstance(other, Vector3):
            raise TypeError("Vector3 cross product requires Vector3")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.vector3_cross,
            result=VECTOR3_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.vector3.cross",
        )
        return Vector3._from_state(self.runtime, state)

    def length(self) -> Scalar:
        state = self.runtime._value_state(
            ops.vector3_length,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector3.length",
        )
        return Scalar._from_state(self.runtime, state)

    def normalized(self) -> Vector3:
        state = self.runtime._value_state(
            ops.vector3_normalized,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vector3.normalized",
        )
        return Vector3._from_state(self.runtime, state)

    def to_ocp(self) -> gp_Vec:
        x, y, z = self.value()
        return gp_Vec(x, y, z)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3):
            return False
        require_same_runtime(self.runtime, other)
        return self.value() == other.value()


def _components2(
    x: ScalarInput | tuple[ScalarInput, ScalarInput],
    y: ScalarInput | None,
) -> tuple[ScalarInput, ScalarInput]:
    if isinstance(x, tuple):
        if y is not None or len(x) != 2:
            raise TypeError("2D value requires exactly two coordinates")
        return x
    if y is None:
        raise TypeError("2D value requires exactly two coordinates")
    return (x, y)


def _components3(
    x: ScalarInput | tuple[ScalarInput, ScalarInput, ScalarInput],
    y: ScalarInput | None,
    z: ScalarInput | None,
) -> tuple[ScalarInput, ScalarInput, ScalarInput]:
    if isinstance(x, tuple):
        if y is not None or z is not None or len(x) != 3:
            raise TypeError("3D value requires exactly three coordinates")
        return x
    if y is None or z is None:
        raise TypeError("3D value requires exactly three coordinates")
    return (x, y, z)


def _unary_math(
    value: Scalar, operation: Callable[[float], float], operation_id: str
) -> Scalar:
    return value._unary(operation, operation_id)


def sin(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_sin, "zencad.typed.math.sin")


def cos(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_cos, "zencad.typed.math.cos")


def tan(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_tan, "zencad.typed.math.tan")


def asin(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_asin, "zencad.typed.math.asin")


def acos(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_acos, "zencad.typed.math.acos")


def atan(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_atan, "zencad.typed.math.atan")


def sqrt(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_sqrt, "zencad.typed.math.sqrt")


def exp(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_exp, "zencad.typed.math.exp")


def log(value: Scalar) -> Scalar:
    return _unary_math(value, ops.scalar_log, "zencad.typed.math.log")


@overload
def atan2(y: Scalar, x: ScalarInput) -> Scalar: ...


@overload
def atan2(y: ScalarInput, x: Scalar) -> Scalar: ...


def atan2(y: ScalarInput, x: ScalarInput) -> Scalar:
    runtime = _infer_runtime(None, (y, x))
    state = runtime._value_state(
        ops.scalar_atan2,
        result=SCALAR_SPEC,
        args=(_scalar_state(runtime, y), _scalar_state(runtime, x)),
        operation_id="zencad.typed.math.atan2",
    )
    return Scalar._from_state(runtime, state)
