"""Typed immutable quaternion and similarity-transform handles."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast, overload

from OCP.TopoDS import TopoDS_Vertex
from OCP.gp import gp_GTrsf, gp_Quaternion, gp_Trsf
from OCP.gp import gp_Dir, gp_Pnt, gp_Vec, gp_XYZ
from evalcache import Expression, ResultSpec

from zencad.occ_compat import vertex_point
from zencad.operation import (
    execution_context,
    operation,
    resolve_context,
    using_context,
)

from . import _transform_operations as ops
from ._core import Handle, State, require_same_context
from ._serialization import AffineTransformSerializer
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR3_SPEC,
    Point3,
    Scalar,
    ScalarInput,
    Vector3,
    _infer_context,
)

if TYPE_CHECKING:
    from .context import Context


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
        context: Context | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        values: tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput],
        *,
        context: Context | None = None,
    ) -> None: ...

    def __init__(
        self,
        x: ScalarInput
        | tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput]
        | ops.QuaternionValue,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        w: ScalarInput | None = None,
        *,
        context: Context | None = None,
    ) -> None:
        if isinstance(x, ops.QuaternionValue):
            if y is not None or z is not None or w is not None:
                raise TypeError("Quaternion expects one resolved value")
            from zencad.operation import execution_context

            selected_context = execution_context() if context is None else context
            self._bind(
                selected_context,
                QUATERNION_SPEC.validate(x, "zencad.typed.quaternion.construct"),
            )
            return
        components = _components4(x, y, z, w)
        resolved_context = _infer_context(context, components)
        with using_context(resolved_context):
            value = quaternion(*components)
        self._bind(value.context, value._state)

    @classmethod
    def _from_state(
        cls,
        context: Context,
        state: State[ops.QuaternionValue],
    ) -> Quaternion:
        if not isinstance(state, Expression):
            state = QUATERNION_SPEC.validate(state, "zencad.typed.quaternion.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def identity(cls, *, context: Context) -> Quaternion:
        return cls(0.0, 0.0, 0.0, 1.0, context=context)

    @classmethod
    def from_ocp(
        cls,
        value: gp_Quaternion,
        *,
        context: Context,
    ) -> Quaternion:
        if not isinstance(value, gp_Quaternion):
            raise TypeError("Quaternion.from_ocp expects gp_Quaternion")
        return cls._from_state(context, ops.quaternion_from_ocp(value))

    def _coordinate(self, axis: int) -> Scalar:
        return _quaternion_coordinate(self, axis)

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
        return _quaternion_compose(self, other)

    def then(self, other: Quaternion) -> Quaternion:
        """Apply this rotation first and ``other`` second."""
        if not isinstance(other, Quaternion):
            raise TypeError("Quaternion.then expects Quaternion")
        return other * self

    def conjugate(self) -> Quaternion:
        return self.inverse()

    def inverse(self) -> Quaternion:
        return _quaternion_inverse(self)

    def normalized(self) -> Quaternion:
        """Return self: construction keeps every Quaternion normalized."""
        return self

    def norm(self) -> Scalar:
        """Return the unit norm while preserving deferred validation."""
        return _quaternion_norm(self)

    def rotate(self, vector: Vector3) -> Vector3:
        if not isinstance(vector, Vector3):
            raise TypeError("Quaternion.rotate expects Vector3")
        return _quaternion_rotate_vector(self, vector)

    def to_transform(self) -> Transform:
        return rotation(self)

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
        require_same_context(self.context, other)
        return self._resolved() == other._resolved()


class Transform(Handle[ops.TransformValue]):
    """Immutable similarity transform containing a resolved value or graph."""

    def __init__(
        self,
        value: ops.TransformValue | None = None,
        *,
        context: Context | None = None,
    ) -> None:
        from zencad.operation import execution_context

        selected_context = execution_context() if context is None else context
        resolved = ops.identity_transform() if value is None else value
        self._bind(
            selected_context,
            TRANSFORM_SPEC.validate(resolved, "zencad.typed.transform.construct"),
        )

    @classmethod
    def _from_state(
        cls,
        context: Context,
        state: State[ops.TransformValue],
    ) -> Transform:
        if not isinstance(state, Expression):
            state = TRANSFORM_SPEC.validate(state, "zencad.typed.transform.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def from_ocp(
        cls,
        value: gp_Trsf,
        *,
        context: Context,
    ) -> Transform:
        if not isinstance(value, gp_Trsf):
            raise TypeError("Transform.from_ocp expects gp_Trsf")
        return cls._from_state(context, ops.transform_from_ocp(value))

    @property
    def scale(self) -> Scalar:
        return _transform_scale(self)

    @property
    def rotation(self) -> Quaternion:
        return _transform_rotation(self)

    @property
    def translation(self) -> Vector3:
        return _transform_translation(self)

    @overload
    def __mul__(self, other: Transform) -> Transform: ...

    @overload
    def __mul__(self, other: AffineTransform) -> AffineTransform: ...

    def __mul__(
        self,
        other: Transform | AffineTransform,
    ) -> Transform | AffineTransform:
        if isinstance(other, AffineTransform):
            require_same_context(self.context, other)
            return self.to_affine() * other
        if not isinstance(other, Transform):
            raise TypeError(
                "Transform can only compose with Transform or AffineTransform"
            )
        return _transform_compose(self, other)

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
        return _transform_inverse(self)

    @overload
    def apply(self, value: Point3, /) -> Point3: ...

    @overload
    def apply(self, value: Vector3, /) -> Vector3: ...

    def apply(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        if not isinstance(value, (Point3, Vector3)):
            raise TypeError("Transform.apply expects Point3 or Vector3")
        if isinstance(value, Point3):
            return _transform_point(self, value)
        return _transform_vector(self, value)

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
        return _transform_rotation_euler(self)

    def rotation_axis_angle(self) -> tuple[Vector3, Scalar]:
        return (
            _transform_rotation_axis(self),
            _transform_rotation_angle(self),
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
        return _affine_from_transform(self)

    def __str__(self) -> str:
        return f"Transform(matrix={self.matrix()!r})"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform):
            return False
        require_same_context(self.context, other)
        return self._resolved() == other._resolved()


class AffineTransform(Handle[ops.AffineTransformValue]):
    """Immutable general affine map with an explicit mutable OCP boundary."""

    def __init__(
        self,
        rows: Sequence[Sequence[ScalarInput]] | ops.AffineTransformValue | None = None,
        *,
        context: Context | None = None,
    ) -> None:
        from zencad.operation import execution_context

        selected_context = execution_context() if context is None else context
        if isinstance(rows, ops.AffineTransformValue):
            self._bind(
                selected_context,
                AFFINE_TRANSFORM_SPEC.validate(rows, "zencad.typed.affine.construct"),
            )
            return
        if rows is None:
            self._bind(selected_context, ops.identity_affine_transform())
            return
        with using_context(selected_context):
            value = affine_transform(rows)
        self._bind(value.context, value._state)

    @classmethod
    def _from_state(
        cls,
        context: Context,
        state: State[ops.AffineTransformValue],
    ) -> AffineTransform:
        if not isinstance(state, Expression):
            state = AFFINE_TRANSFORM_SPEC.validate(state, "zencad.typed.affine.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def identity(cls, *, context: Context) -> AffineTransform:
        return cls(context=context)

    @classmethod
    def from_ocp(
        cls,
        value: gp_GTrsf,
        *,
        context: Context,
    ) -> AffineTransform:
        if not isinstance(value, gp_GTrsf):
            raise TypeError("AffineTransform.from_ocp expects gp_GTrsf")
        return cls._from_state(context, ops.affine_from_ocp(value))

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
        context: Context,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_context(context):
            return scaleXYZ(x, y, z, center=center)

    @classmethod
    def scaleX(
        cls,
        factor: ScalarInput,
        /,
        *,
        context: Context,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_context(context):
            return scaleX(factor, center=center)

    @classmethod
    def scaleY(
        cls,
        factor: ScalarInput,
        /,
        *,
        context: Context,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_context(context):
            return scaleY(factor, center=center)

    @classmethod
    def scaleZ(
        cls,
        factor: ScalarInput,
        /,
        *,
        context: Context,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_context(context):
            return scaleZ(factor, center=center)

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
        return _affine_compose(self, other)

    @overload
    def then(self, other: AffineTransform) -> AffineTransform: ...

    @overload
    def then(self, other: Transform) -> AffineTransform: ...

    def then(self, other: AffineTransform | Transform) -> AffineTransform:
        if not isinstance(other, (AffineTransform, Transform)):
            raise TypeError("AffineTransform.then expects AffineTransform or Transform")
        return other * self

    def inverse(self) -> AffineTransform:
        return _affine_inverse(self)

    @overload
    def apply(self, value: Point3, /) -> Point3: ...

    @overload
    def apply(self, value: Vector3, /) -> Vector3: ...

    def apply(self, value: Point3 | Vector3, /) -> Point3 | Vector3:
        if not isinstance(value, (Point3, Vector3)):
            raise TypeError("AffineTransform.apply expects Point3 or Vector3")
        if isinstance(value, Point3):
            return _affine_point(self, value)
        return _affine_vector(self, value)

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
        return _affine_translation(self)

    @property
    def determinant(self) -> Scalar:
        return _affine_determinant(self)

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
        require_same_context(self.context, other)
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
    rows: Sequence[Sequence[float]],
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
    float,
    float,
    float,
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


@operation(
    result=QUATERNION_SPEC,
    returns=Quaternion,
    operation_id="zencad.typed.quaternion",
    operation_version="1",
    fold_literals=True,
)
def quaternion(
    x: float,
    y: float,
    z: float,
    w: float,
    /,
) -> Quaternion:
    return Quaternion(
        ops.quaternion(
            _number(x, "quaternion x"),
            _number(y, "quaternion y"),
            _number(z, "quaternion z"),
            _number(w, "quaternion w"),
        )
    )


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.quaternion.coordinate",
    operation_version="1",
    fold_literals=True,
)
def _quaternion_coordinate(
    value: Quaternion,
    axis: int,
    /,
) -> Scalar:
    if not isinstance(value, Quaternion):
        raise TypeError("quaternion coordinate expects Quaternion")
    if isinstance(axis, bool) or not isinstance(axis, int) or not 0 <= axis <= 3:
        raise ValueError("quaternion coordinate axis must be between 0 and 3")
    return Scalar(ops.quaternion_coordinate(value._resolved(), axis))


@operation(
    result=QUATERNION_SPEC,
    returns=Quaternion,
    operation_id="zencad.typed.quaternion.axis_angle",
    operation_version="1",
    fold_literals=True,
)
def quaternion_axis_angle(
    axis: Vector3,
    angle: float,
    /,
) -> Quaternion:
    if not isinstance(axis, Vector3):
        raise TypeError("quaternion_axis_angle expects Vector3")
    return Quaternion(ops.quaternion_axis_angle(axis._resolved(), angle))


@operation(
    result=QUATERNION_SPEC,
    returns=Quaternion,
    operation_id="zencad.typed.quaternion.compose",
    operation_version="1",
    fold_literals=True,
)
def _quaternion_compose(
    left: Quaternion,
    right: Quaternion,
    /,
) -> Quaternion:
    _require_pair(left, right, Quaternion, "Quaternion composition")
    return Quaternion(ops.quaternion_compose(left._resolved(), right._resolved()))


@operation(
    result=QUATERNION_SPEC,
    returns=Quaternion,
    operation_id="zencad.typed.quaternion.inverse",
    operation_version="1",
    fold_literals=True,
)
def _quaternion_inverse(value: Quaternion, /) -> Quaternion:
    _require_type(value, Quaternion, "quaternion inverse")
    return Quaternion(ops.quaternion_inverse(value._resolved()))


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.quaternion.norm",
    operation_version="1",
    fold_literals=True,
)
def _quaternion_norm(value: Quaternion, /) -> Scalar:
    _require_type(value, Quaternion, "quaternion norm")
    return Scalar(ops.quaternion_norm(value._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.quaternion.rotate_vector",
    operation_version="1",
    fold_literals=True,
)
def _quaternion_rotate_vector(
    value: Quaternion,
    vector: Vector3,
    /,
) -> Vector3:
    _require_type(value, Quaternion, "quaternion rotation")
    _require_type(vector, Vector3, "quaternion rotation vector")
    return Vector3(ops.quaternion_rotate_vector(value._resolved(), vector._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.identity",
    operation_version="1",
    fold_literals=True,
)
def identity_transform() -> Transform:
    return Transform(ops.identity_transform())


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.translation",
    operation_version="1",
    fold_literals=True,
)
def translation(
    vector: Vector3 | float,
    y: float | None = None,
    z: float | None = None,
    /,
) -> Transform:
    if isinstance(vector, Vector3):
        if y is not None or z is not None:
            raise TypeError("translation Vector3 cannot be combined with coordinates")
        resolved_vector = vector
    elif y is not None and z is not None:
        resolved_vector = Vector3(vector, y, z)
    else:
        raise TypeError("translation expects Vector3 or three scalar coordinates")
    return Transform(ops.translation_transform(resolved_vector._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.rotation",
    operation_version="1",
    fold_literals=True,
)
def rotation(
    quaternion: Quaternion | Vector3,
    angle: float | None = None,
    /,
) -> Transform:
    if isinstance(quaternion, Quaternion):
        if angle is not None:
            raise TypeError("rotation Quaternion cannot be combined with an angle")
        resolved_quaternion = quaternion
    elif isinstance(quaternion, Vector3) and angle is not None:
        resolved_quaternion = Quaternion(
            ops.quaternion_axis_angle(quaternion._resolved(), angle)
        )
    else:
        raise TypeError("rotation expects Quaternion or Vector3 and angle")
    return Transform(ops.rotation_transform(resolved_quaternion._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.scale",
    operation_version="1",
    fold_literals=True,
)
def scale(
    factor: float,
    /,
    *,
    center: Point3 | None = None,
) -> Transform:
    resolved_center = _scale_center(execution_context(), center, "scale")
    return Transform(ops.scale_transform(factor, resolved_center._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.mirror",
    operation_version="1",
    fold_literals=True,
)
def mirror(
    normal: Vector3,
    /,
    *,
    origin: Point3 | None = None,
) -> Transform:
    _require_type(normal, Vector3, "mirror normal")
    context = resolve_context(normal, origin)
    resolved_origin = _scale_center(context, origin, "mirror")
    return Transform(
        ops.mirror_transform(normal._resolved(), resolved_origin._resolved())
    )


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.shortest_rotation",
    operation_version="1",
    fold_literals=True,
)
def short_rotate(
    source: Vector3 | Sequence[float],
    target: Vector3 | Sequence[float],
    /,
) -> Transform:
    resolved_source = source if isinstance(source, Vector3) else Vector3(tuple(source))
    resolved_target = target if isinstance(target, Vector3) else Vector3(tuple(target))
    return Transform(
        ops.shortest_rotation_transform(
            resolved_source._resolved(), resolved_target._resolved()
        )
    )


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.transform.scale_value",
    operation_version="1",
    fold_literals=True,
)
def _transform_scale(value: Transform, /) -> Scalar:
    _require_type(value, Transform, "transform scale")
    return Scalar(ops.transform_scale(value._resolved()))


@operation(
    result=QUATERNION_SPEC,
    returns=Quaternion,
    operation_id="zencad.typed.transform.rotation_value",
    operation_version="1",
    fold_literals=True,
)
def _transform_rotation(value: Transform, /) -> Quaternion:
    _require_type(value, Transform, "transform rotation")
    return Quaternion(ops.transform_rotation(value._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.transform.translation_value",
    operation_version="1",
    fold_literals=True,
)
def _transform_translation(value: Transform, /) -> Vector3:
    _require_type(value, Transform, "transform translation")
    return Vector3(ops.transform_translation(value._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.compose",
    operation_version="1",
    fold_literals=True,
)
def _transform_compose(
    left: Transform,
    right: Transform,
    /,
) -> Transform:
    _require_pair(left, right, Transform, "Transform composition")
    return Transform(ops.transform_compose(left._resolved(), right._resolved()))


@operation(
    result=TRANSFORM_SPEC,
    returns=Transform,
    operation_id="zencad.typed.transform.inverse",
    operation_version="1",
    fold_literals=True,
)
def _transform_inverse(value: Transform, /) -> Transform:
    _require_type(value, Transform, "transform inverse")
    return Transform(ops.transform_inverse(value._resolved()))


@operation(
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.transform.point",
    operation_version="1",
    fold_literals=True,
)
def _transform_point(
    transform: Transform,
    point: Point3,
    /,
) -> Point3:
    _require_type(transform, Transform, "point transform")
    _require_type(point, Point3, "transformed point")
    return Point3(ops.transform_point(transform._resolved(), point._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.transform.vector",
    operation_version="1",
    fold_literals=True,
)
def _transform_vector(
    transform: Transform,
    vector: Vector3,
    /,
) -> Vector3:
    _require_type(transform, Transform, "vector transform")
    _require_type(vector, Vector3, "transformed vector")
    return Vector3(ops.transform_vector(transform._resolved(), vector._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.transform.rotation_euler",
    operation_version="1",
    fold_literals=True,
)
def _transform_rotation_euler(value: Transform, /) -> Vector3:
    _require_type(value, Transform, "transform rotation_euler")
    return Vector3(ops.transform_rotation_vector(value._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.transform.rotation_axis",
    operation_version="1",
    fold_literals=True,
)
def _transform_rotation_axis(value: Transform, /) -> Vector3:
    _require_type(value, Transform, "transform rotation axis")
    return Vector3(ops.transform_rotation_axis(value._resolved()))


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.transform.rotation_angle",
    operation_version="1",
    fold_literals=True,
)
def _transform_rotation_angle(value: Transform, /) -> Scalar:
    _require_type(value, Transform, "transform rotation angle")
    return Scalar(ops.transform_rotation_angle(value._resolved()))


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.identity",
    operation_version="1",
    fold_literals=True,
)
def identity_affine_transform() -> AffineTransform:
    return AffineTransform(ops.identity_affine_transform())


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.matrix",
    operation_version="1",
    fold_literals=True,
)
def affine_transform(
    rows: Sequence[Sequence[float]],
    /,
) -> AffineTransform:
    components = _matrix3x4_components(rows)
    return AffineTransform(ops.affine_transform(*components))


def affine(rows: Sequence[Sequence[float]], /) -> AffineTransform:
    return affine_transform(rows)


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.from_transform",
    operation_version="1",
    fold_literals=True,
)
def _affine_from_transform(value: Transform, /) -> AffineTransform:
    _require_type(value, Transform, "affine conversion")
    return AffineTransform(ops.affine_from_transform(value._resolved()))


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.scale_xyz",
    operation_version="1",
    fold_literals=True,
)
def scaleXYZ(
    x: float,
    y: float,
    z: float,
    /,
    *,
    center: Point3 | None = None,
) -> AffineTransform:
    resolved_center = _scale_center(execution_context(), center, "affine scale")
    return AffineTransform(
        ops.affine_scale_transform(x, y, z, resolved_center._resolved())
    )


def scaleX(
    factor: ScalarInput,
    /,
    *,
    center: Point3 | None = None,
) -> AffineTransform:
    return scaleXYZ(factor, 1, 1, center=center)


def scaleY(
    factor: ScalarInput,
    /,
    *,
    center: Point3 | None = None,
) -> AffineTransform:
    return scaleXYZ(1, factor, 1, center=center)


def scaleZ(
    factor: ScalarInput,
    /,
    *,
    center: Point3 | None = None,
) -> AffineTransform:
    return scaleXYZ(1, 1, factor, center=center)


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.compose",
    operation_version="1",
    fold_literals=True,
)
def _affine_compose(
    left: AffineTransform,
    right: AffineTransform,
    /,
) -> AffineTransform:
    _require_pair(left, right, AffineTransform, "AffineTransform composition")
    return AffineTransform(ops.affine_compose(left._resolved(), right._resolved()))


@operation(
    result=AFFINE_TRANSFORM_SPEC,
    returns=AffineTransform,
    operation_id="zencad.typed.affine.inverse",
    operation_version="1",
    fold_literals=True,
)
def _affine_inverse(value: AffineTransform, /) -> AffineTransform:
    _require_type(value, AffineTransform, "affine inverse")
    return AffineTransform(ops.affine_inverse(value._resolved()))


@operation(
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.affine.point",
    operation_version="1",
    fold_literals=True,
)
def _affine_point(
    transform: AffineTransform,
    point: Point3,
    /,
) -> Point3:
    _require_type(transform, AffineTransform, "affine point transform")
    _require_type(point, Point3, "affine transformed point")
    return Point3(ops.affine_point(transform._resolved(), point._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.affine.vector",
    operation_version="1",
    fold_literals=True,
)
def _affine_vector(
    transform: AffineTransform,
    vector: Vector3,
    /,
) -> Vector3:
    _require_type(transform, AffineTransform, "affine vector transform")
    _require_type(vector, Vector3, "affine transformed vector")
    return Vector3(ops.affine_vector(transform._resolved(), vector._resolved()))


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.affine.translation",
    operation_version="1",
    fold_literals=True,
)
def _affine_translation(value: AffineTransform, /) -> Vector3:
    _require_type(value, AffineTransform, "affine translation")
    return Vector3(ops.affine_translation(value._resolved()))


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.affine.determinant",
    operation_version="1",
    fold_literals=True,
)
def _affine_determinant(value: AffineTransform, /) -> Scalar:
    _require_type(value, AffineTransform, "affine determinant")
    return Scalar(ops.affine_determinant(value._resolved()))


def move(*args: object) -> Transform:
    context = resolve_context(args)
    return translation(_compat_vector3(context, args, "move"))


def translate(*args: object) -> Transform:
    return move(*args)


def moveX(value: ScalarInput, /) -> Transform:
    return move(value, 0, 0)


def moveY(value: ScalarInput, /) -> Transform:
    return move(0, value, 0)


def moveZ(value: ScalarInput, /) -> Transform:
    return move(0, 0, value)


movX = moveX
movY = moveY
movZ = moveZ
translateX = moveX
translateY = moveY
translateZ = moveZ
right = moveX
forw = moveY
up = moveZ


def left(value: ScalarInput, /) -> Transform:
    context = resolve_context(value)
    return moveX(-_as_scalar(context, value))


def back(value: ScalarInput, /) -> Transform:
    context = resolve_context(value)
    return moveY(-_as_scalar(context, value))


def down(value: ScalarInput, /) -> Transform:
    context = resolve_context(value)
    return moveZ(-_as_scalar(context, value))


def rotate(
    axis: Vector3 | Sequence[ScalarInput],
    angle: ScalarInput | None = None,
    /,
) -> Transform:
    context = resolve_context(axis, angle)
    resolved_axis = _compat_vector3(context, (axis,), "rotate")
    if angle is None:
        angle = resolved_axis.length()
        resolved_axis = resolved_axis.normalized()
    return rotation(resolved_axis, angle)


def rotate_quat(
    value: Quaternion | gp_Quaternion | Sequence[ScalarInput],
    /,
) -> Transform:
    context = resolve_context(value)
    return rotation(_compat_quaternion(context, value))


def rotateX(angle: ScalarInput, /) -> Transform:
    context = resolve_context(angle)
    return rotate(Vector3(1, 0, 0, context=context), angle)


def rotateY(angle: ScalarInput, /) -> Transform:
    context = resolve_context(angle)
    return rotate(Vector3(0, 1, 0, context=context), angle)


def rotateZ(angle: ScalarInput, /) -> Transform:
    context = resolve_context(angle)
    return rotate(Vector3(0, 0, 1, context=context), angle)


def mirror_plane(*normal: object) -> Transform:
    context = resolve_context(normal)
    return mirror(_compat_vector3(context, normal, "mirror_plane"))


def mirrorXY() -> Transform:
    return mirror_plane(0, 0, 1)


def mirrorYZ() -> Transform:
    return mirror_plane(1, 0, 0)


def mirrorXZ() -> Transform:
    return mirror_plane(0, 1, 0)


def mirror_axis(*axis: object) -> Transform:
    context = resolve_context(axis)
    return rotate(_compat_vector3(context, axis, "mirror_axis"), 3.141592653589793)


def mirrorX() -> Transform:
    return mirror_axis(1, 0, 0)


def mirrorY() -> Transform:
    return mirror_axis(0, 1, 0)


def mirrorZ() -> Transform:
    return mirror_axis(0, 0, 1)


def mirrorO(*origin: object) -> Transform:
    context = resolve_context(origin)
    return scale(-1, center=_compat_point3(context, origin, "mirrorO"))


def nulltrans() -> Transform:
    return identity_transform()


def _scale_center(
    context: Context,
    center: Point3 | None,
    name: str,
) -> Point3:
    if center is None:
        return Point3(0, 0, 0, context=context)
    if not isinstance(center, Point3):
        raise TypeError(f"{name} center must be Point3")
    require_same_context(context, center)
    return center


def _require_type(value: object, expected: type[object], name: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{name} expects {expected.__name__}")


def _number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float")
    return float(value)


def _require_pair(
    left: object,
    right: object,
    expected: type[object],
    name: str,
) -> None:
    _require_type(left, expected, name)
    _require_type(right, expected, name)


def _as_scalar(context: Context, value: ScalarInput) -> Scalar:
    if isinstance(value, Scalar):
        require_same_context(context, value)
        return value
    return Scalar(value, context=context)


def _compat_vector3(
    context: Context,
    args: tuple[object, ...],
    name: str,
) -> Vector3:
    if len(args) == 1 and isinstance(args[0], Vector3):
        require_same_context(context, args[0])
        return args[0]
    components = _compat_components3(context, args, name)
    return Vector3(*components, context=context)


def _compat_point3(
    context: Context,
    args: tuple[object, ...],
    name: str,
) -> Point3:
    if len(args) == 1 and isinstance(args[0], Point3):
        require_same_context(context, args[0])
        return args[0]
    components = _compat_components3(context, args, name)
    return Point3(*components, context=context)


def _compat_components3(
    context: Context,
    args: tuple[object, ...],
    name: str,
) -> tuple[ScalarInput, ScalarInput, ScalarInput]:
    if not args:
        values: tuple[object, ...] = ()
    elif len(args) == 1:
        value = args[0]
        if isinstance(value, (Point3, Vector3)):
            require_same_context(context, value)
            values = (value.x, value.y, value.z)
        elif isinstance(value, TopoDS_Vertex):
            point = vertex_point(value)
            values = (point.X(), point.Y(), point.Z())
        elif isinstance(value, (gp_Pnt, gp_Dir, gp_Vec, gp_XYZ)):
            values = (value.X(), value.Y(), value.Z())
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values = tuple(value)
        else:
            values = (value,)
    else:
        values = args
    if len(values) > 3:
        raise TypeError(f"{name} expects at most three coordinates")
    padded = values + (0,) * (3 - len(values))
    return (
        cast(ScalarInput, padded[0]),
        cast(ScalarInput, padded[1]),
        cast(ScalarInput, padded[2]),
    )


def _compat_quaternion(
    context: Context,
    value: Quaternion | gp_Quaternion | Sequence[ScalarInput],
) -> Quaternion:
    if isinstance(value, Quaternion):
        require_same_context(context, value)
        return value
    if isinstance(value, gp_Quaternion):
        return Quaternion.from_ocp(value, context=context)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        components = tuple(value)
        if len(components) == 4:
            return quaternion(
                *cast(
                    tuple[ScalarInput, ScalarInput, ScalarInput, ScalarInput],
                    components,
                )
            )
    raise TypeError("rotate_quat expects Quaternion, gp_Quaternion, or four components")


__all__ = [
    "AFFINE_TRANSFORM_SPEC",
    "AffineTransform",
    "GeneralTransformation",
    "QUATERNION_SPEC",
    "Quaternion",
    "TRANSFORM_SPEC",
    "Transform",
    "affine",
    "affine_transform",
    "back",
    "down",
    "forw",
    "identity_affine_transform",
    "identity_transform",
    "left",
    "mirror",
    "mirrorO",
    "mirrorX",
    "mirrorXY",
    "mirrorXZ",
    "mirrorY",
    "mirrorYZ",
    "mirrorZ",
    "mirror_axis",
    "mirror_plane",
    "movX",
    "movY",
    "movZ",
    "move",
    "moveX",
    "moveY",
    "moveZ",
    "nulltrans",
    "quaternion",
    "quaternion_axis_angle",
    "right",
    "rotate",
    "rotateX",
    "rotateY",
    "rotateZ",
    "rotate_quat",
    "rotation",
    "scale",
    "scaleX",
    "scaleXYZ",
    "scaleY",
    "scaleZ",
    "short_rotate",
    "translate",
    "translateX",
    "translateY",
    "translateZ",
    "translation",
    "up",
]
