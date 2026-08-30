"""Typed immutable quaternion and similarity-transform handles."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from OCP.gp import gp_Quaternion, gp_Trsf
from evalcache.v2 import ResultSpec

from . import _transform_operations as ops
from ._core import Handle, State, require_same_runtime
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR3_SPEC,
    Point3,
    Scalar,
    ScalarInput,
    Vector3,
    _infer_runtime,
    _scalar_state,
)

if TYPE_CHECKING:
    from .runtime import Runtime


QUATERNION_SPEC = ResultSpec.for_type(
    ops.QuaternionValue,
    type_id="zencad.typed.Quaternion.v1",
)
TRANSFORM_SPEC = ResultSpec.for_type(
    ops.TransformValue,
    type_id="zencad.typed.Transform.v1",
)


class Quaternion(Handle[ops.QuaternionValue]):
    """Unit rotation quaternion with graph-aware components."""

    @overload
    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        w: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput],
        *,
        runtime: Runtime | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput | tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput],
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        w: ScalarInput | None = None,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        components = _components4(x, y, z, w)
        resolved_runtime = _infer_runtime(runtime, components)
        state = resolved_runtime._value_state(
            ops.quaternion,
            result=QUATERNION_SPEC,
            args=tuple(
                _scalar_state(resolved_runtime, component) for component in components
            ),
            operation_id="zencad.typed.quaternion",
        )
        self._bind(resolved_runtime, state)

    @classmethod
    def _from_state(
        cls,
        runtime: Runtime,
        state: State[ops.QuaternionValue],
    ) -> Quaternion:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def identity(cls, *, runtime: Runtime) -> Quaternion:
        return cls(0.0, 0.0, 0.0, 1.0, runtime=runtime)

    @classmethod
    def from_ocp(
        cls,
        value: gp_Quaternion,
        *,
        runtime: Runtime,
    ) -> Quaternion:
        if not isinstance(value, gp_Quaternion):
            raise TypeError("Quaternion.from_ocp expects gp_Quaternion")
        return cls._from_state(runtime, ops.quaternion_from_ocp(value))

    def _coordinate(self, axis: int) -> Scalar:
        state = self.runtime._value_state(
            ops.quaternion_coordinate,
            result=SCALAR_SPEC,
            args=(self._state, axis),
            operation_id="zencad.typed.quaternion.coordinate",
        )
        return Scalar._from_state(self.runtime, state)

    @property
    def x(self) -> Scalar:
        return self._coordinate(0)

    @property
    def y(self) -> Scalar:
        return self._coordinate(1)

    @property
    def z(self) -> Scalar:
        return self._coordinate(2)

    @property
    def w(self) -> Scalar:
        return self._coordinate(3)

    def __mul__(self, other: Quaternion) -> Quaternion:
        if not isinstance(other, Quaternion):
            raise TypeError("Quaternion can only compose with Quaternion")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.quaternion_compose,
            result=QUATERNION_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.quaternion.compose",
        )
        return Quaternion._from_state(self.runtime, state)

    def then(self, other: Quaternion) -> Quaternion:
        """Apply this rotation first and ``other`` second."""
        if not isinstance(other, Quaternion):
            raise TypeError("Quaternion.then expects Quaternion")
        return other * self

    def conjugate(self) -> Quaternion:
        return self.inverse()

    def inverse(self) -> Quaternion:
        state = self.runtime._value_state(
            ops.quaternion_inverse,
            result=QUATERNION_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.quaternion.inverse",
        )
        return Quaternion._from_state(self.runtime, state)

    def normalized(self) -> Quaternion:
        """Return self: construction keeps every Quaternion normalized."""
        return self

    def norm(self) -> Scalar:
        """Return the unit norm while preserving deferred validation."""
        state = self.runtime._value_state(
            ops.quaternion_norm,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.quaternion.norm",
        )
        return Scalar._from_state(self.runtime, state)

    def rotate(self, vector: Vector3) -> Vector3:
        if not isinstance(vector, Vector3):
            raise TypeError("Quaternion.rotate expects Vector3")
        require_same_runtime(self.runtime, vector)
        state = self.runtime._value_state(
            ops.quaternion_rotate_vector,
            result=VECTOR3_SPEC,
            args=(self._state, vector._state),
            operation_id="zencad.typed.quaternion.rotate_vector",
        )
        return Vector3._from_state(self.runtime, state)

    def to_transform(self) -> Transform:
        state = self.runtime._value_state(
            ops.rotation_transform,
            result=TRANSFORM_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.rotation",
        )
        return Transform._from_state(self.runtime, state)

    def value(self) -> tuple[float, float, float, float]:
        value = self._resolved()
        return (value.x, value.y, value.z, value.w)

    def to_ocp(self) -> gp_Quaternion:
        """Materialize a fresh mutable OCP quaternion."""
        return ops.quaternion_to_ocp(self._resolved())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quaternion):
            return False
        require_same_runtime(self.runtime, other)
        return self._resolved() == other._resolved()


class Transform(Handle[ops.TransformValue]):
    """Immutable similarity transform containing a resolved value or graph."""

    def __init__(self, *, runtime: Runtime) -> None:
        self._bind(runtime, ops.identity_transform())

    @classmethod
    def _from_state(
        cls,
        runtime: Runtime,
        state: State[ops.TransformValue],
    ) -> Transform:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_ocp(
        cls,
        value: gp_Trsf,
        *,
        runtime: Runtime,
    ) -> Transform:
        if not isinstance(value, gp_Trsf):
            raise TypeError("Transform.from_ocp expects gp_Trsf")
        return cls._from_state(runtime, ops.transform_from_ocp(value))

    @property
    def scale(self) -> Scalar:
        state = self.runtime._value_state(
            ops.transform_scale,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.scale_value",
        )
        return Scalar._from_state(self.runtime, state)

    @property
    def rotation(self) -> Quaternion:
        state = self.runtime._value_state(
            ops.transform_rotation,
            result=QUATERNION_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.rotation_value",
        )
        return Quaternion._from_state(self.runtime, state)

    @property
    def translation(self) -> Vector3:
        state = self.runtime._value_state(
            ops.transform_translation,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.translation_value",
        )
        return Vector3._from_state(self.runtime, state)

    def __mul__(self, other: Transform) -> Transform:
        if not isinstance(other, Transform):
            raise TypeError("Transform can only compose with Transform")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.transform_compose,
            result=TRANSFORM_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.transform.compose",
        )
        return Transform._from_state(self.runtime, state)

    def then(self, other: Transform) -> Transform:
        """Apply this transform first and ``other`` second."""
        if not isinstance(other, Transform):
            raise TypeError("Transform.then expects Transform")
        return other * self

    def inverse(self) -> Transform:
        state = self.runtime._value_state(
            ops.transform_inverse,
            result=TRANSFORM_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.inverse",
        )
        return Transform._from_state(self.runtime, state)

    @overload
    def apply(self, value: Point3, /) -> Point3: ...

    @overload
    def apply(self, value: Vector3, /) -> Vector3: ...

    def apply(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        if not isinstance(value, (Point3, Vector3)):
            raise TypeError("Transform.apply expects Point3 or Vector3")
        require_same_runtime(self.runtime, value)
        if isinstance(value, Point3):
            state = self.runtime._value_state(
                ops.transform_point,
                result=POINT3_SPEC,
                args=(self._state, value._state),
                operation_id="zencad.typed.transform.point",
            )
            return Point3._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.transform_vector,
            result=VECTOR3_SPEC,
            args=(self._state, value._state),
            operation_id="zencad.typed.transform.vector",
        )
        return Vector3._from_state(self.runtime, state)

    @overload
    def __call__(self, value: Point3, /) -> Point3: ...

    @overload
    def __call__(self, value: Vector3, /) -> Vector3: ...

    def __call__(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        return self.apply(value)

    def matrix(
        self,
    ) -> tuple[
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
    ]:
        """Materialize a conventional homogeneous 4x4 matrix."""
        value = ops.transform_matrix(self._resolved())
        return (
            (value[0], value[1], value[2], value[3]),
            (value[4], value[5], value[6], value[7]),
            (value[8], value[9], value[10], value[11]),
            (0.0, 0.0, 0.0, 1.0),
        )

    def to_ocp(self) -> gp_Trsf:
        """Materialize a fresh mutable OCP transform."""
        return ops.transform_to_ocp(self._resolved())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform):
            return False
        require_same_runtime(self.runtime, other)
        return self._resolved() == other._resolved()


def _components4(
    x: ScalarInput | tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput],
    y: ScalarInput | None,
    z: ScalarInput | None,
    w: ScalarInput | None,
) -> tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput]:
    if isinstance(x, tuple):
        if y is not None or z is not None or w is not None or len(x) != 4:
            raise TypeError("Quaternion expects four components")
        return x
    if y is None or z is None or w is None:
        raise TypeError("Quaternion expects four components")
    return (x, y, z, w)
