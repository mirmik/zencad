"""Experimental typed ZenCad domain handles.

This module is intentionally private.  It is the vertical slice used to prove
that a stable domain API can contain an evalcache expression graph without
exposing lazy proxy types to callers.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Callable, TypeVar, cast, overload

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

from . import _operations as ops
from . import _bound_operations as bound_ops
from . import _curve_operations as curve_ops
from . import _surface_operations as surface_ops
from . import _transform_operations as transform_ops
from ._core import State, require_same_runtime
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .curves import CURVE2_SPEC, CURVE_SPEC, Curve, Curve2
from .surfaces import SURFACE_SPEC, Surface, SweepTrihedron
from .topology import (
    EDGE_SPEC,
    FACE_SPEC,
    SOLID_SPEC,
    WIRE_SPEC,
    Compound,
    CompSolid,
    DeferredSequence,
    Edge,
    Face,
    Shape,
    Shell,
    Solid,
    Vertex,
    Wire,
)
from .transforms import (
    QUATERNION_SPEC,
    TRANSFORM_SPEC,
    Quaternion,
    Transform,
)
from .values import (
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

__all__ = [
    "Compound",
    "CompSolid",
    "BoundaryBox",
    "Curve",
    "Curve2",
    "DeferredSequence",
    "Edge",
    "Face",
    "Runtime",
    "Shape",
    "Shell",
    "Solid",
    "Surface",
    "SweepTrihedron",
    "Vertex",
    "Wire",
]


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

    @overload
    def box(
        self,
        size: Vector3,
        /,
        *,
        center: bool = False,
    ) -> Solid: ...

    @overload
    def box(
        self,
        x: ScalarInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        *,
        center: bool = False,
    ) -> Solid: ...

    def box(
        self,
        x: ScalarInput | Vector3,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        *,
        center: bool = False,
    ) -> Solid:
        _require_bool(center, "box center")
        if isinstance(x, Vector3):
            if y is not None or z is not None:
                raise TypeError("box Vector3 size cannot be combined with y or z")
            require_same_runtime(self, x)
            size = x
        else:
            if y is None and z is None:
                size = Vector3(x, x, x, runtime=self)
            elif y is not None and z is not None:
                size = Vector3(x, y, z, runtime=self)
            else:
                raise TypeError("box expects one size or all three dimensions")
        expression = self._expression(
            ops.box,
            result=SOLID_SPEC,
            args=(size._state, center),
            operation_id="zencad.typed.box",
        )
        return Solid._from_state(self, expression)

    def sphere(self, radius: ScalarInput, /) -> Solid:
        expression = self._expression(
            ops.sphere,
            result=SOLID_SPEC,
            args=(_scalar_state(self, radius),),
            operation_id="zencad.typed.sphere",
        )
        return Solid._from_state(self, expression)

    def empty_boundary_box(self) -> BoundaryBox:
        """Return the identity value for boundary-box union."""
        return BoundaryBox._from_state(self, bound_ops.empty_boundary_box())

    def boundary_box(self, minimum: Point3, maximum: Point3, /) -> BoundaryBox:
        """Create a graph-preserving box from its opposite corner points."""
        if not isinstance(minimum, Point3) or not isinstance(maximum, Point3):
            raise TypeError("boundary_box expects Point3 corners")
        require_same_runtime(self, minimum)
        require_same_runtime(self, maximum)
        state = self._value_state(
            bound_ops.boundary_box_from_points,
            result=BOUNDARY_BOX_SPEC,
            args=(minimum._state, maximum._state),
            operation_id="zencad.typed.boundary-box.from-points",
        )
        return BoundaryBox._from_state(self, state)

    def line(self, origin: Point3, direction: Vector3, /) -> Curve:
        if not isinstance(origin, Point3):
            raise TypeError("line origin must be Point3")
        if not isinstance(direction, Vector3):
            raise TypeError("line direction must be Vector3")
        require_same_runtime(self, origin)
        require_same_runtime(self, direction)
        expression = self._expression(
            curve_ops.line,
            result=CURVE_SPEC,
            args=(origin._state, direction._state),
            operation_id="zencad.typed.line",
        )
        return Curve._from_state(self, expression)

    def circle(self, radius: ScalarInput, /) -> Curve:
        expression = self._expression(
            curve_ops.circle,
            result=CURVE_SPEC,
            args=(_scalar_state(self, radius),),
            operation_id="zencad.typed.circle",
        )
        return Curve._from_state(self, expression)

    def ellipse(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve:
        expression = self._expression(
            curve_ops.ellipse,
            result=CURVE_SPEC,
            args=(
                _scalar_state(self, major_radius),
                _scalar_state(self, minor_radius),
            ),
            operation_id="zencad.typed.ellipse",
        )
        return Curve._from_state(self, expression)

    def segment2(self, start: Point2, end: Point2, /) -> Curve2:
        if not isinstance(start, Point2) or not isinstance(end, Point2):
            raise TypeError("segment2 expects Point2 endpoints")
        require_same_runtime(self, start)
        require_same_runtime(self, end)
        expression = self._expression(
            curve_ops.segment2,
            result=CURVE2_SPEC,
            args=(start._state, end._state),
            operation_id="zencad.typed.segment2",
        )
        return Curve2._from_state(self, expression)

    def ellipse2(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve2:
        expression = self._expression(
            curve_ops.ellipse2,
            result=CURVE2_SPEC,
            args=(
                _scalar_state(self, major_radius),
                _scalar_state(self, minor_radius),
            ),
            operation_id="zencad.typed.ellipse2",
        )
        return Curve2._from_state(self, expression)

    def trim_curve2(
        self,
        curve: Curve2,
        start: ScalarInput,
        end: ScalarInput,
        /,
    ) -> Curve2:
        if not isinstance(curve, Curve2):
            raise TypeError("trim_curve2 expects Curve2")
        require_same_runtime(self, curve)
        expression = self._expression(
            curve_ops.trim_curve2,
            result=CURVE2_SPEC,
            args=(
                curve._state,
                _scalar_state(self, start),
                _scalar_state(self, end),
            ),
            operation_id="zencad.typed.trim_curve2",
        )
        return Curve2._from_state(self, expression)

    def cylinder_surface(self, radius: ScalarInput, /) -> Surface:
        expression = self._expression(
            surface_ops.cylinder_surface,
            result=SURFACE_SPEC,
            args=(_scalar_state(self, radius),),
            operation_id="zencad.typed.cylinder_surface",
        )
        return Surface._from_state(self, expression)

    def sweep_surface(
        self,
        section: Curve,
        spine: Curve,
        /,
        *,
        scale: ScalarInput = 1,
        trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET,
        tolerance: Number = 1e-6,
        continuity: int = 2,
        max_degree: int = 5,
        max_segments: int = 20,
    ) -> Surface:
        if not isinstance(section, Curve):
            raise TypeError("sweep_surface section must be Curve")
        if not isinstance(spine, Curve):
            raise TypeError("sweep_surface spine must be Curve")
        require_same_runtime(self, section)
        require_same_runtime(self, spine)
        if not isinstance(trihedron, SweepTrihedron):
            raise TypeError("sweep_surface trihedron must be SweepTrihedron")
        resolved_tolerance = _require_positive_number(
            tolerance,
            "sweep_surface tolerance",
        )
        resolved_continuity = _require_int_between(
            continuity,
            "sweep_surface continuity",
            minimum=0,
            maximum=3,
        )
        resolved_max_degree = _require_positive_int(
            max_degree,
            "sweep_surface max_degree",
        )
        resolved_max_segments = _require_positive_int(
            max_segments,
            "sweep_surface max_segments",
        )
        expression = self._expression(
            surface_ops.sweep_surface,
            result=SURFACE_SPEC,
            args=(
                section._state,
                spine._state,
                _scalar_state(self, scale),
                trihedron.value,
                resolved_tolerance,
                resolved_continuity,
                resolved_max_degree,
                resolved_max_segments,
            ),
            operation_id="zencad.typed.sweep_surface",
        )
        return Surface._from_state(self, expression)

    def segment(self, start: Point3, end: Point3, /) -> Edge:
        _require_points(self, (start, end), minimum=2, name="segment")
        expression = self._expression(
            ops.segment,
            result=EDGE_SPEC,
            args=(start._state, end._state),
            operation_id="zencad.typed.segment",
        )
        return Edge._from_state(self, expression)

    def polysegment(
        self,
        points: Sequence[Point3],
        /,
        *,
        closed: bool = False,
    ) -> Wire:
        _require_bool(closed, "polysegment closed")
        values = _require_points(self, points, minimum=2, name="polysegment")
        expression = self._expression(
            ops.polysegment,
            result=WIRE_SPEC,
            args=(tuple(point._state for point in values), closed),
            operation_id="zencad.typed.polysegment",
        )
        return Wire._from_state(self, expression)

    def polygon(self, points: Sequence[Point3], /) -> Face:
        values = _require_points(self, points, minimum=3, name="polygon")
        expression = self._expression(
            ops.polygon,
            result=FACE_SPEC,
            args=(tuple(point._state for point in values),),
            operation_id="zencad.typed.polygon",
        )
        return Face._from_state(self, expression)

    def rectangle(
        self,
        width: ScalarInput,
        height: ScalarInput | None = None,
        /,
        *,
        center: bool = False,
    ) -> Face:
        _require_bool(center, "rectangle center")
        resolved_height = width if height is None else height
        expression = self._expression(
            ops.rectangle,
            result=FACE_SPEC,
            args=(
                _scalar_state(self, width),
                _scalar_state(self, resolved_height),
                center,
            ),
            operation_id="zencad.typed.rectangle",
        )
        return Face._from_state(self, expression)

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


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_positive_number(value: Number, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _require_positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _require_int_between(
    value: int,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _require_points(
    runtime: Runtime,
    points: Sequence[Point3],
    *,
    minimum: int,
    name: str,
) -> tuple[Point3, ...]:
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise TypeError(f"{name} expects a sequence of Point3")
    values = tuple(points)
    if len(values) < minimum:
        raise ValueError(f"{name} requires at least {minimum} points")
    if not all(isinstance(point, Point3) for point in values):
        raise TypeError(f"{name} expects only Point3 values")
    for point in values:
        require_same_runtime(runtime, point)
    return values
