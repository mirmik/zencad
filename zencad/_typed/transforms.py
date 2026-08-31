"""Typed immutable quaternion and similarity-transform handles."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, overload

from OCP.gp import gp_GTrsf, gp_Quaternion, gp_Trsf
from evalcache import ResultSpec

from . import _transform_operations as ops
from ._core import Handle, State, require_same_runtime
from ._serialization import AffineTransformSerializer
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
_AFFINE_TRANSFORM_SERIALIZER = AffineTransformSerializer()
AFFINE_TRANSFORM_SPEC = ResultSpec.for_type(
    ops.AffineTransformValue,
    type_id="zencad.typed.AffineTransform.v1",
    serializer=_AFFINE_TRANSFORM_SERIALIZER,
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

    def __str__(self) -> str:
        x, y, z, w = self.value()
        return f"quat({x},{y},{z},{w})"

    def __repr__(self) -> str:
        return str(self)

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

    @overload
    def __mul__(self, other: Transform) -> Transform: ...

    @overload
    def __mul__(self, other: AffineTransform) -> AffineTransform: ...

    def __mul__(
        self,
        other: Transform | AffineTransform,
    ) -> Transform | AffineTransform:
        if isinstance(other, AffineTransform):
            require_same_runtime(self.runtime, other)
            return self.to_affine() * other
        if not isinstance(other, Transform):
            raise TypeError("Transform can only compose with Transform or AffineTransform")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.transform_compose,
            result=TRANSFORM_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.transform.compose",
        )
        return Transform._from_state(self.runtime, state)

    @overload
    def then(self, other: Transform) -> Transform: ...

    @overload
    def then(self, other: AffineTransform) -> AffineTransform: ...

    def then(
        self,
        other: Transform | AffineTransform,
    ) -> Transform | AffineTransform:
        """Apply this transform first and ``other`` second."""
        if not isinstance(other, (Transform, AffineTransform)):
            raise TypeError("Transform.then expects Transform or AffineTransform")
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

    def transform_point(self, point: Point3, /) -> Point3:
        if not isinstance(point, Point3):
            raise TypeError("Transform.transform_point expects Point3")
        return self.apply(point)

    def transform_vector(self, vector: Vector3, /) -> Vector3:
        if not isinstance(vector, Vector3):
            raise TypeError("Transform.transform_vector expects Vector3")
        return self.apply(vector)

    def inverse_transform_point(self, point: Point3, /) -> Point3:
        return self.inverse().transform_point(point)

    def inverse_transform_vector(self, vector: Vector3, /) -> Vector3:
        return self.inverse().transform_vector(vector)

    def rotation_quat(self) -> Quaternion:
        return self.rotation

    def rotation_euler(self) -> Vector3:
        state = self.runtime._value_state(
            ops.transform_rotation_vector,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.rotation_euler",
        )
        return Vector3._from_state(self.runtime, state)

    def rotation_axis_angle(self) -> tuple[Vector3, Scalar]:
        axis_state = self.runtime._value_state(
            ops.transform_rotation_axis,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.rotation_axis",
        )
        angle_state = self.runtime._value_state(
            ops.transform_rotation_angle,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.transform.rotation_angle",
        )
        return (
            Vector3._from_state(self.runtime, axis_state),
            Scalar._from_state(self.runtime, angle_state),
        )

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

    def to_affine(self) -> AffineTransform:
        state = self.runtime._value_state(
            ops.affine_from_transform,
            result=AFFINE_TRANSFORM_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.affine.from_transform",
        )
        return AffineTransform._from_state(self.runtime, state)

    def __str__(self) -> str:
        return f"Transform(matrix={self.matrix()!r})"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform):
            return False
        require_same_runtime(self.runtime, other)
        return self._resolved() == other._resolved()


class AffineTransform(Handle[ops.AffineTransformValue]):
    """Immutable general affine map with an explicit mutable OCP boundary."""

    def __init__(
        self,
        rows: Sequence[Sequence[ScalarInput]] | None = None,
        *,
        runtime: Runtime,
    ) -> None:
        if rows is None:
            self._bind(runtime, ops.identity_affine_transform())
            return
        components = _matrix3x4_components(rows)
        state = runtime._value_state(
            ops.affine_transform,
            result=AFFINE_TRANSFORM_SPEC,
            args=tuple(_scalar_state(runtime, component) for component in components),
            operation_id="zencad.typed.affine.matrix",
        )
        self._bind(runtime, state)

    @classmethod
    def _from_state(
        cls,
        runtime: Runtime,
        state: State[ops.AffineTransformValue],
    ) -> AffineTransform:
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def identity(cls, *, runtime: Runtime) -> AffineTransform:
        return cls(runtime=runtime)

    @classmethod
    def from_ocp(
        cls,
        value: gp_GTrsf,
        *,
        runtime: Runtime,
    ) -> AffineTransform:
        if not isinstance(value, gp_GTrsf):
            raise TypeError("AffineTransform.from_ocp expects gp_GTrsf")
        return cls._from_state(runtime, ops.affine_from_ocp(value))

    @classmethod
    def from_transform(cls, value: Transform, /) -> AffineTransform:
        if not isinstance(value, Transform):
            raise TypeError("AffineTransform.from_transform expects Transform")
        return value.to_affine()

    @classmethod
    def scaleXYZ(
        cls,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
        *,
        runtime: Runtime,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return runtime.scaleXYZ(x, y, z, center=center)

    @classmethod
    def scaleX(
        cls,
        factor: ScalarInput,
        /,
        *,
        runtime: Runtime,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return runtime.scaleX(factor, center=center)

    @classmethod
    def scaleY(
        cls,
        factor: ScalarInput,
        /,
        *,
        runtime: Runtime,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return runtime.scaleY(factor, center=center)

    @classmethod
    def scaleZ(
        cls,
        factor: ScalarInput,
        /,
        *,
        runtime: Runtime,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return runtime.scaleZ(factor, center=center)

    @overload
    def __mul__(self, other: AffineTransform) -> AffineTransform: ...

    @overload
    def __mul__(self, other: Transform) -> AffineTransform: ...

    def __mul__(self, other: AffineTransform | Transform) -> AffineTransform:
        if isinstance(other, Transform):
            other = other.to_affine()
        if not isinstance(other, AffineTransform):
            raise TypeError(
                "AffineTransform can only compose with AffineTransform or Transform"
            )
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.affine_compose,
            result=AFFINE_TRANSFORM_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.affine.compose",
        )
        return AffineTransform._from_state(self.runtime, state)

    @overload
    def then(self, other: AffineTransform) -> AffineTransform: ...

    @overload
    def then(self, other: Transform) -> AffineTransform: ...

    def then(self, other: AffineTransform | Transform) -> AffineTransform:
        if not isinstance(other, (AffineTransform, Transform)):
            raise TypeError("AffineTransform.then expects AffineTransform or Transform")
        return other * self

    def inverse(self) -> AffineTransform:
        state = self.runtime._value_state(
            ops.affine_inverse,
            result=AFFINE_TRANSFORM_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.affine.inverse",
        )
        return AffineTransform._from_state(self.runtime, state)

    @overload
    def apply(self, value: Point3, /) -> Point3: ...

    @overload
    def apply(self, value: Vector3, /) -> Vector3: ...

    def apply(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        if not isinstance(value, (Point3, Vector3)):
            raise TypeError("AffineTransform.apply expects Point3 or Vector3")
        require_same_runtime(self.runtime, value)
        if isinstance(value, Point3):
            state = self.runtime._value_state(
                ops.affine_point,
                result=POINT3_SPEC,
                args=(self._state, value._state),
                operation_id="zencad.typed.affine.point",
            )
            return Point3._from_state(self.runtime, state)
        state = self.runtime._value_state(
            ops.affine_vector,
            result=VECTOR3_SPEC,
            args=(self._state, value._state),
            operation_id="zencad.typed.affine.vector",
        )
        return Vector3._from_state(self.runtime, state)

    @overload
    def __call__(self, value: Point3, /) -> Point3: ...

    @overload
    def __call__(self, value: Vector3, /) -> Vector3: ...

    def __call__(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        return self.apply(value)

    def transform_point(self, point: Point3, /) -> Point3:
        if not isinstance(point, Point3):
            raise TypeError("AffineTransform.transform_point expects Point3")
        return self.apply(point)

    def transform_vector(self, vector: Vector3, /) -> Vector3:
        if not isinstance(vector, Vector3):
            raise TypeError("AffineTransform.transform_vector expects Vector3")
        return self.apply(vector)

    @property
    def translation(self) -> Vector3:
        state = self.runtime._value_state(
            ops.affine_translation,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.affine.translation",
        )
        return Vector3._from_state(self.runtime, state)

    @property
    def determinant(self) -> Scalar:
        state = self.runtime._value_state(
            ops.affine_determinant,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.affine.determinant",
        )
        return Scalar._from_state(self.runtime, state)

    def matrix(
        self,
    ) -> tuple[
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
    ]:
        value = self._resolved().components
        return (
            (value[0], value[1], value[2], value[3]),
            (value[4], value[5], value[6], value[7]),
            (value[8], value[9], value[10], value[11]),
            (0.0, 0.0, 0.0, 1.0),
        )

    def to_ocp(self) -> gp_GTrsf:
        """Materialize a fresh mutable OCP general transformation."""
        return ops.affine_to_ocp(self._resolved())

    def __str__(self) -> str:
        return f"AffineTransform(matrix={self.matrix()!r})"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AffineTransform):
            return False
        require_same_runtime(self.runtime, other)
        return self._resolved() == other._resolved()


GeneralTransformation = AffineTransform


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


def _matrix3x4_components(
    rows: Sequence[Sequence[ScalarInput]],
) -> tuple[
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
    ScalarInput,
]:
    if len(rows) != 3 or any(len(row) != 4 for row in rows):
        raise ValueError("AffineTransform expects a 3x4 matrix")
    return (
        rows[0][0],
        rows[0][1],
        rows[0][2],
        rows[0][3],
        rows[1][0],
        rows[1][1],
        rows[1][2],
        rows[1][3],
        rows[2][0],
        rows[2][1],
        rows[2][2],
        rows[2][3],
    )
