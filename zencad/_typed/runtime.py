"""Experimental typed ZenCad domain handles.

This module is intentionally private.  It is the vertical slice used to prove
that a stable domain API can contain an evalcache expression graph without
exposing lazy proxy types to callers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Callable, Generic, TypeVar, Union, cast, overload

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
from ._serialization import ShapeBrepSerializer


ResolvedT = TypeVar("ResolvedT")
ShapeHandleT = TypeVar("ShapeHandleT", bound="Shape")
Number = int | float
ScalarInput = Union[Number, "Scalar"]


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
_SCALAR_SPEC = ResultSpec.for_type(float, type_id="zencad.typed.Scalar.v1")
_POINT_SPEC = ResultSpec.for_type(ops.PointValue, type_id="zencad.typed.Point3.v1")
_VECTOR_SPEC = ResultSpec.for_type(ops.VectorValue, type_id="zencad.typed.Vector3.v1")


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


class _Handle(Generic[ResolvedT]):
    __slots__ = ("_runtime", "_expression")

    def _bind(self, runtime: Runtime, expression: Expression[ResolvedT]) -> None:
        self._runtime = runtime
        self._expression = expression

    @property
    def runtime(self) -> Runtime:
        return self._runtime

    def _resolved(self) -> ResolvedT:
        return self._runtime._resolve(self._expression)

    def unlazy(self):
        """Compatibility boundary: materialize but preserve the handle type."""
        self._resolved()
        return self


class Scalar(_Handle[float]):
    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[float]
    ) -> Scalar:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value

    def value(self) -> float:
        return self._resolved()

    def __float__(self) -> float:
        return self.value()

    def _binary(
        self,
        other: ScalarInput,
        operation: Callable[[float, float], float],
        operation_id: str,
    ) -> Scalar:
        argument = _scalar_argument(self.runtime, other)
        expression = self.runtime._expression(
            operation,
            result=_SCALAR_SPEC,
            args=(self._expression, argument),
            operation_id=operation_id,
        )
        return Scalar._from_expression(self.runtime, expression)

    def __add__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_add, "zencad.typed.scalar.add")

    def __sub__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_subtract, "zencad.typed.scalar.subtract")

    def __mul__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_multiply, "zencad.typed.scalar.multiply")

    def __truediv__(self, other: ScalarInput) -> Scalar:
        return self._binary(other, ops.scalar_divide, "zencad.typed.scalar.divide")


class _XYZHandle(_Handle[ResolvedT], Generic[ResolvedT]):
    def _coordinate_function(self) -> Callable[[ResolvedT, int], float]:
        raise NotImplementedError

    def _coordinate(self, axis: int) -> Scalar:
        expression = self.runtime._expression(
            self._coordinate_function(),
            result=_SCALAR_SPEC,
            args=(self._expression, axis),
            operation_id=f"zencad.typed.{type(self).__name__.lower()}.coordinate",
        )
        return Scalar._from_expression(self.runtime, expression)

    @property
    def x(self) -> Scalar:
        return self._coordinate(0)

    @property
    def y(self) -> Scalar:
        return self._coordinate(1)

    @property
    def z(self) -> Scalar:
        return self._coordinate(2)


class Point3(_XYZHandle[ops.PointValue]):
    def _coordinate_function(
        self,
    ) -> Callable[[ops.PointValue, int], float]:
        return ops.point_coordinate

    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        resolved_runtime = _infer_runtime(runtime, (x, y, z))
        expression = resolved_runtime._expression(
            ops.point,
            result=_POINT_SPEC,
            args=tuple(_scalar_argument(resolved_runtime, item) for item in (x, y, z)),
            operation_id="zencad.typed.point3",
        )
        self._bind(resolved_runtime, expression)

    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[ops.PointValue]
    ) -> Point3:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value

    def value(self) -> tuple[float, float, float]:
        point = self._resolved()
        return (point.x, point.y, point.z)


class Vector3(_XYZHandle[ops.VectorValue]):
    def _coordinate_function(
        self,
    ) -> Callable[[ops.VectorValue, int], float]:
        return ops.vector_coordinate

    def __init__(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        resolved_runtime = _infer_runtime(runtime, (x, y, z))
        expression = resolved_runtime._expression(
            ops.vector,
            result=_VECTOR_SPEC,
            args=tuple(_scalar_argument(resolved_runtime, item) for item in (x, y, z)),
            operation_id="zencad.typed.vector3",
        )
        self._bind(resolved_runtime, expression)

    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[ops.VectorValue]
    ) -> Vector3:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value

    def value(self) -> tuple[float, float, float]:
        vector = self._resolved()
        return (vector.x, vector.y, vector.z)


class Shape(_Handle[ResolvedShape]):
    @classmethod
    def _from_expression(
        cls, runtime: Runtime, expression: Expression[ResolvedShape]
    ) -> Shape:
        value = cls.__new__(cls)
        value._bind(runtime, expression)
        return value

    def __sub__(self, other: Shape) -> Shape:
        _require_same_runtime(self.runtime, other)
        expression = self.runtime._expression(
            ops.difference,
            result=_SHAPE_SPEC,
            args=(self._expression, other._expression),
            operation_id="zencad.typed.shape.difference",
        )
        return Shape._from_expression(self.runtime, expression)

    @overload
    def translate(self, vector: Vector3, /) -> Shape: ...

    @overload
    def translate(self, x: ScalarInput, y: ScalarInput, z: ScalarInput, /) -> Shape: ...

    def translate(self, *args: object) -> Shape:
        if len(args) == 1 and isinstance(args[0], Vector3):
            vector = args[0]
            _require_same_runtime(self.runtime, vector)
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
            args=(self._expression, vector._expression),
            operation_id="zencad.typed.shape.translate",
        )
        return Shape._from_expression(self.runtime, expression)

    def faces(self) -> DeferredSequence[Face]:
        expression = self.runtime._expression(
            ops.faces,
            result=_FACE_SEQUENCE_SPEC,
            args=(self._expression,),
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
        expression = self.runtime._expression(
            ops.mass,
            result=_SCALAR_SPEC,
            args=(self._expression,),
            operation_id="zencad.typed.shape.mass",
        )
        return Scalar._from_expression(self.runtime, expression)

    def center(self) -> Point3:
        expression = self.runtime._expression(
            ops.center,
            result=_POINT_SPEC,
            args=(self._expression,),
            operation_id="zencad.typed.shape.center",
        )
        return Point3._from_expression(self.runtime, expression)

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


def _infer_runtime(
    explicit: Runtime | None, values: tuple[ScalarInput, ...]
) -> Runtime:
    runtimes = {value.runtime for value in values if isinstance(value, Scalar)}
    if explicit is not None:
        runtimes.add(explicit)
    if not runtimes:
        raise TypeError("literal Point3/Vector3 construction requires runtime=")
    if len(runtimes) != 1:
        raise ValueError("cannot mix handles from different typed runtimes")
    return next(iter(runtimes))


def _scalar_argument(runtime: Runtime, value: ScalarInput) -> object:
    if isinstance(value, Scalar):
        _require_same_runtime(runtime, value)
        return value._expression
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("expected Scalar, int, or float")
    return float(value)


def _require_same_runtime(runtime: Runtime, handle: _Handle[ResolvedT]) -> None:
    if handle.runtime is not runtime:
        raise ValueError("cannot mix handles from different typed runtimes")
