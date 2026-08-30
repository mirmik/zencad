"""Experimental typed ZenCad domain handles.

This module is intentionally private.  It is the vertical slice used to prove
that a stable domain API can contain an evalcache expression graph without
exposing lazy proxy types to callers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Callable, Generic, TypeVar, cast, overload

from OCP.TopoDS import TopoDS_Shape
from evalcache.v2 import (
    CachePolicy,
    CacheStore,
    EvaluationMode,
    Evaluator,
    Expression,
    MappingCacheStore,
    ProgressHook,
    ResultSpec,
)

from zencad.geom.shape import Shape as ResolvedShape

from . import _operations as ops
from . import _transform_operations as transform_ops
from ._core import Handle, State, require_same_runtime
from ._serialization import ShapeBrepSerializer
from .transforms import (
    QUATERNION_SPEC,
    TRANSFORM_SPEC,
    Quaternion,
    Transform,
)
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    Number,
    Point2,
    Point3,
    Scalar,
    ScalarInput,
    Vector2,
    Vector3,
    _scalar_state,
)


ResolvedT = TypeVar("ResolvedT")
ShapeHandleT = TypeVar("ShapeHandleT", bound="Shape")


_SHAPE_SERIALIZER = ShapeBrepSerializer()
_SHAPE_SPEC = ResultSpec.for_type(
    ResolvedShape,
    type_id="zencad.typed.Shape.v1",
    serializer=_SHAPE_SERIALIZER,
)
_FACE_SPEC = ResultSpec.for_type(
    ResolvedShape,
    type_id="zencad.typed.Face.v1",
    serializer=_SHAPE_SERIALIZER,
    validator=lambda shape: shape.is_face(),
)
_FACE_SEQUENCE_SPEC = ResultSpec.for_type(
    tuple,
    type_id="zencad.typed.Sequence[Face].v1",
    validator=lambda values: all(
        isinstance(value, ResolvedShape) and value.is_face() for value in values
    ),
)


class Runtime:
    """Own one expression evaluator and its independent cache policy."""

    CACHE_NAMESPACE = "zencad-typed-v1"

    def __init__(
        self,
        *,
        mode: EvaluationMode | str = EvaluationMode.DEFERRED,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> None:
        resolved_mode = EvaluationMode(mode)
        if cache:
            policy = CachePolicy(namespace=self.CACHE_NAMESPACE)
            if cache_store is None:
                from zencad.lazifier import lazy

                cache_store = MappingCacheStore(lazy.cache)
        else:
            policy = CachePolicy.disabled(namespace=self.CACHE_NAMESPACE)
            cache_store = None
        self._evaluator = Evaluator(
            mode=resolved_mode,
            cache_policy=policy,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def deferred(
        cls,
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> Runtime:
        return cls(
            mode=EvaluationMode.DEFERRED,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def immediate(
        cls,
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> Runtime:
        return cls(
            mode=EvaluationMode.IMMEDIATE,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @property
    def mode(self) -> EvaluationMode:
        return self._evaluator.mode

    @property
    def cache_enabled(self) -> bool:
        return self._evaluator.cache_policy.enabled

    def _expression(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
        cacheable: bool = True,
    ) -> Expression[ResolvedT]:
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version="1",
            cacheable=cacheable,
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            self._evaluator.evaluate(expression)
        return expression

    def _resolve(self, expression: Expression[ResolvedT]) -> ResolvedT:
        return self._evaluator.evaluate(expression)

    def _value_state(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
    ) -> State[ResolvedT]:
        """Fold resolved value operands; otherwise retain a typed expression."""
        if all(not isinstance(argument, Expression) for argument in args):
            value = operation(*args)
            return result.validate(value, operation_id)
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version="1",
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            return self._evaluator.evaluate(expression)
        return expression

    def box(
        self,
        x: Number,
        y: Number | None = None,
        z: Number | None = None,
        *,
        center: bool = False,
    ) -> Shape:
        expression = self._expression(
            ops.box,
            result=_SHAPE_SPEC,
            args=(float(x), _optional_float(y), _optional_float(z), center),
            operation_id="zencad.typed.box",
        )
        return Shape._from_expression(self, expression)

    def point(self, x: ScalarInput, y: ScalarInput, z: ScalarInput) -> Point3:
        return Point3(x, y, z, runtime=self)

    def vector(self, x: ScalarInput, y: ScalarInput, z: ScalarInput) -> Vector3:
        return Vector3(x, y, z, runtime=self)

    def scalar(self, value: Number) -> Scalar:
        return Scalar(value, runtime=self)

    def point2(self, x: ScalarInput, y: ScalarInput) -> Point2:
        return Point2(x, y, runtime=self)

    def vector2(self, x: ScalarInput, y: ScalarInput) -> Vector2:
        return Vector2(x, y, runtime=self)

    def quaternion(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        w: ScalarInput,
    ) -> Quaternion:
        return Quaternion(x, y, z, w, runtime=self)

    def quaternion_axis_angle(
        self,
        axis: Vector3,
        angle: ScalarInput,
        /,
    ) -> Quaternion:
        if not isinstance(axis, Vector3):
            raise TypeError("quaternion_axis_angle expects Vector3")
        require_same_runtime(self, axis)
        state = self._value_state(
            transform_ops.quaternion_axis_angle,
            result=QUATERNION_SPEC,
            args=(axis._state, _scalar_state(self, angle)),
            operation_id="zencad.typed.quaternion.axis_angle",
        )
        return Quaternion._from_state(self, state)

    def identity_transform(self) -> Transform:
        return Transform(runtime=self)

    @overload
    def translation(self, vector: Vector3, /) -> Transform: ...

    @overload
    def translation(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
    ) -> Transform: ...

    def translation(self, *args: object) -> Transform:
        if len(args) == 1 and isinstance(args[0], Vector3):
            vector = args[0]
            require_same_runtime(self, vector)
        elif len(args) == 3:
            vector = Vector3(
                cast(ScalarInput, args[0]),
                cast(ScalarInput, args[1]),
                cast(ScalarInput, args[2]),
                runtime=self,
            )
        else:
            raise TypeError("translation expects Vector3 or three scalar coordinates")
        state = self._value_state(
            transform_ops.translation_transform,
            result=TRANSFORM_SPEC,
            args=(vector._state,),
            operation_id="zencad.typed.transform.translation",
        )
        return Transform._from_state(self, state)

    @overload
    def rotation(self, quaternion: Quaternion, /) -> Transform: ...

    @overload
    def rotation(
        self,
        axis: Vector3,
        angle: ScalarInput,
        /,
    ) -> Transform: ...

    def rotation(self, *args: object) -> Transform:
        if len(args) == 1 and isinstance(args[0], Quaternion):
            quaternion = args[0]
            require_same_runtime(self, quaternion)
        elif len(args) == 2 and isinstance(args[0], Vector3):
            quaternion = self.quaternion_axis_angle(args[0], cast(ScalarInput, args[1]))
        else:
            raise TypeError("rotation expects Quaternion or Vector3 and angle")
        return quaternion.to_transform()

    def scale(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> Transform:
        if center is None:
            center = self.point(0, 0, 0)
        elif not isinstance(center, Point3):
            raise TypeError("scale center must be Point3")
        require_same_runtime(self, center)
        state = self._value_state(
            transform_ops.scale_transform,
            result=TRANSFORM_SPEC,
            args=(_scalar_state(self, factor), center._state),
            operation_id="zencad.typed.transform.scale",
        )
        return Transform._from_state(self, state)

    def mirror(
        self,
        normal: Vector3,
        /,
        *,
        origin: Point3 | None = None,
    ) -> Transform:
        if not isinstance(normal, Vector3):
            raise TypeError("mirror normal must be Vector3")
        if origin is None:
            origin = self.point(0, 0, 0)
        elif not isinstance(origin, Point3):
            raise TypeError("mirror origin must be Point3")
        require_same_runtime(self, normal)
        require_same_runtime(self, origin)
        state = self._value_state(
            transform_ops.mirror_transform,
            result=TRANSFORM_SPEC,
            args=(normal._state, origin._state),
            operation_id="zencad.typed.transform.mirror",
        )
        return Transform._from_state(self, state)


class Shape(Handle[ResolvedShape]):
    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[ResolvedShape]
    ) -> Shape:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value

    def __sub__(self, other: Shape) -> Shape:
        require_same_runtime(self.runtime, other)
        expression = self.runtime._expression(
            ops.difference,
            result=_SHAPE_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.shape.difference",
        )
        return Shape._from_expression(self.runtime, expression)

    def transform(self, transformation: Transform, /) -> Shape:
        if not isinstance(transformation, Transform):
            raise TypeError("Shape.transform expects Transform")
        require_same_runtime(self.runtime, transformation)
        expression = self.runtime._expression(
            ops.transform,
            result=_SHAPE_SPEC,
            args=(self._state, transformation._state),
            operation_id="zencad.typed.shape.transform",
        )
        return Shape._from_expression(self.runtime, expression)

    @overload
    def translate(self, vector: Vector3, /) -> Shape: ...

    @overload
    def translate(self, x: ScalarInput, y: ScalarInput, z: ScalarInput, /) -> Shape: ...

    def translate(self, *args: object) -> Shape:
        if len(args) == 1 and isinstance(args[0], Vector3):
            vector = args[0]
            require_same_runtime(self.runtime, vector)
        elif len(args) == 3:
            vector = Vector3(
                cast(ScalarInput, args[0]),
                cast(ScalarInput, args[1]),
                cast(ScalarInput, args[2]),
                runtime=self.runtime,
            )
        else:
            raise TypeError("translate expects Vector3 or three scalar coordinates")
        expression = self.runtime._expression(
            ops.translate,
            result=_SHAPE_SPEC,
            args=(self._state, vector._state),
            operation_id="zencad.typed.shape.translate",
        )
        return Shape._from_expression(self.runtime, expression)

    def faces(self) -> DeferredSequence[Face]:
        expression = self.runtime._expression(
            ops.faces,
            result=_FACE_SEQUENCE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.faces",
            cacheable=False,
        )
        return DeferredSequence(
            self.runtime,
            expression,
            item_type=Face,
            item_spec=_FACE_SPEC,
            operation_id="zencad.typed.shape.faces.item",
        )

    def mass(self) -> Scalar:
        state = self.runtime._value_state(
            ops.mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.mass",
        )
        return Scalar._from_state(self.runtime, state)

    def center(self) -> Point3:
        state = self.runtime._value_state(
            ops.center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.center",
        )
        return Point3._from_state(self.runtime, state)

    def native(self) -> TopoDS_Shape:
        """Materialize at the explicit OCP boundary."""
        return self._resolved().Shape()

    def _legacy(self) -> ResolvedShape:
        """Temporary adapter for existing internal display/export code."""
        return self._resolved()


class Face(Shape):
    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[ResolvedShape]
    ) -> Face:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value


class DeferredSequence(Generic[ShapeHandleT]):
    """Typed topology sequence whose indexing composes an expression node."""

    def __init__(
        self,
        runtime: Runtime,
        expression: Expression[tuple[ResolvedShape, ...]],
        *,
        item_type: type[ShapeHandleT],
        item_spec: ResultSpec[ResolvedShape],
        operation_id: str,
    ) -> None:
        self._runtime = runtime
        self._expression = expression
        self._item_type = item_type
        self._item_spec = item_spec
        self._operation_id = operation_id

    def __getitem__(self, index: int) -> ShapeHandleT:
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("typed sequence indices must be integers")
        expression = self._runtime._expression(
            ops.sequence_item,
            result=self._item_spec,
            args=(self._expression, index),
            operation_id=self._operation_id,
        )
        return self._item_type._from_expression(self._runtime, expression)

    def __len__(self) -> int:
        return len(self._runtime._resolve(self._expression))

    def __iter__(self) -> Iterator[ShapeHandleT]:
        for index in range(len(self)):
            yield self[index]


def _optional_float(value: Number | None) -> float | None:
    return None if value is None else float(value)
