"""Typed 3D and 2D curve handles containing ZenCad's evaluation graph."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal, TypeVar, cast

from OCP.Geom import Geom_Curve
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.Geom2d import Geom2d_Curve
from evalcache import Expression, ResultSpec

from . import _curve_operations as ops
from ._core import Handle, State, require_same_runtime
from ._serialization import Curve2Serializer, CurveSerializer
from .records import CircleParameters, EllipseParameters, Interval, LineParameters
from .values import (
    POINT2_SPEC,
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR2_SPEC,
    VECTOR3_SPEC,
    Point2,
    Point3,
    Scalar,
    ScalarInput,
    Vector2,
    Vector3,
    _scalar_state,
)

if TYPE_CHECKING:
    from .runtime import Runtime
    from .topology import Edge
    from .transforms import Transform


CurveHandleT = TypeVar("CurveHandleT", bound="Curve")
Curve2HandleT = TypeVar("Curve2HandleT", bound="Curve2")

_CURVE_SERIALIZER = CurveSerializer()
_CURVE2_SERIALIZER = Curve2Serializer()

CURVE_SPEC = ResultSpec.for_type(
    ops.CurveValue,
    type_id="zencad.typed.Curve.v2",
    serializer=_CURVE_SERIALIZER,
    validator=ops.valid_curve,
)
CURVE2_SPEC = ResultSpec.for_type(
    ops.Curve2Value,
    type_id="zencad.typed.Curve2.v2",
    serializer=_CURVE2_SERIALIZER,
    validator=ops.valid_curve2,
)
CURVE_KIND_SPEC = ResultSpec.for_type(
    str,
    type_id="zencad.typed.CurveKind.v1",
    validator=lambda value: (
        value
        in {
            "line",
            "circle",
            "ellipse",
            "hyperbola",
            "parabola",
            "bezier",
            "bspline",
            "offset",
            "other",
        }
    ),
)
LINE_PARAMETERS_SPEC = ResultSpec.for_type(
    ops.LineParametersValue,
    type_id="zencad.typed.LineParameters.v1",
)
CIRCLE_PARAMETERS_SPEC = ResultSpec.for_type(
    ops.CircleParametersValue,
    type_id="zencad.typed.CircleParameters.v1",
)
ELLIPSE_PARAMETERS_SPEC = ResultSpec.for_type(
    ops.EllipseParametersValue,
    type_id="zencad.typed.EllipseParameters.v1",
)
SCALAR_SEQUENCE_SPEC = cast(
    ResultSpec[tuple[float, ...]],
    ResultSpec.for_type(tuple, type_id="zencad.typed.Sequence[Scalar].v1"),
)

CurveKind = Literal[
    "line",
    "circle",
    "ellipse",
    "hyperbola",
    "parabola",
    "bezier",
    "bspline",
    "offset",
    "other",
]


class Curve(Handle[ops.CurveValue]):
    """Stable three-dimensional curve backed by a snapshot or expression."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ops.CurveValue]] = CURVE_SPEC

    @classmethod
    def _from_state(
        cls: type[CurveHandleT],
        runtime: Runtime,
        state: State[ops.CurveValue],
    ) -> CurveHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.curve.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_ocp(
        cls: type[CurveHandleT],
        value: Geom_Curve,
        *,
        runtime: Runtime,
    ) -> CurveHandleT:
        """Copy a mutable OCP curve into an immutable typed snapshot."""
        return cls._from_state(runtime, ops.curve_from_ocp(value))

    def point(self, parameter: ScalarInput, /) -> Point3:
        state = self.runtime._value_state(
            ops.curve_point,
            result=POINT3_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.curve.point",
        )
        return Point3._from_state(self.runtime, state)

    def d0(self, parameter: ScalarInput, /) -> Point3:
        return self.point(parameter)

    def value(self, parameter: ScalarInput, /) -> Point3:
        return self.point(parameter)

    def tangent(self, parameter: ScalarInput, /) -> Vector3:
        """Return the first derivative vector at ``parameter``."""
        state = self.runtime._value_state(
            ops.curve_tangent,
            result=VECTOR3_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.curve.tangent",
        )
        return Vector3._from_state(self.runtime, state)

    def d1(self, parameter: ScalarInput, /) -> Vector3:
        return self.tangent(parameter)

    def range(self) -> Interval:
        first = self.runtime._value_state(
            ops.curve_first_parameter,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.first_parameter",
        )
        last = self.runtime._value_state(
            ops.curve_last_parameter,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.last_parameter",
        )
        return Interval(
            Scalar._from_state(self.runtime, first),
            Scalar._from_state(self.runtime, last),
        )

    def curvetype(self) -> CurveKind:
        state = self.runtime._value_state(
            ops.curve_kind,
            result=CURVE_KIND_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.kind",
        )
        if isinstance(state, Expression):
            state = self.runtime._resolve(state)
        return cast(CurveKind, state)

    def endpoints(self) -> tuple[Point3, Point3]:
        parameters = self.range()
        return (self.point(parameters.lower), self.point(parameters.upper))

    def line_parameters(self) -> LineParameters:
        state = self.runtime._value_state(
            ops.curve_line_parameters,
            result=LINE_PARAMETERS_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.line_parameters",
        )
        origin = self.runtime._value_state(
            ops.line_parameters_origin,
            result=POINT3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.line_parameters.origin",
        )
        direction = self.runtime._value_state(
            ops.line_parameters_direction,
            result=VECTOR3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.line_parameters.direction",
        )
        return LineParameters(
            Point3._from_state(self.runtime, origin),
            Vector3._from_state(self.runtime, direction),
        )

    def circle_parameters(self) -> CircleParameters:
        state = self.runtime._value_state(
            ops.curve_circle_parameters,
            result=CIRCLE_PARAMETERS_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.circle_parameters",
        )
        center = self.runtime._value_state(
            ops.circle_parameters_center,
            result=POINT3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.circle_parameters.center",
        )
        radius = self.runtime._value_state(
            ops.circle_parameters_radius,
            result=SCALAR_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.circle_parameters.radius",
        )
        x_direction = self.runtime._value_state(
            ops.circle_parameters_x_direction,
            result=VECTOR3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.circle_parameters.x_direction",
        )
        y_direction = self.runtime._value_state(
            ops.circle_parameters_y_direction,
            result=VECTOR3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.circle_parameters.y_direction",
        )
        return CircleParameters(
            Point3._from_state(self.runtime, center),
            Scalar._from_state(self.runtime, radius),
            Vector3._from_state(self.runtime, x_direction),
            Vector3._from_state(self.runtime, y_direction),
        )

    def ellipse_parameters(self) -> EllipseParameters:
        state = self.runtime._value_state(
            ops.curve_ellipse_parameters,
            result=ELLIPSE_PARAMETERS_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve.ellipse_parameters",
        )
        center = self.runtime._value_state(
            ops.ellipse_parameters_center,
            result=POINT3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.ellipse_parameters.center",
        )
        major_radius = self.runtime._value_state(
            ops.ellipse_parameters_major_radius,
            result=SCALAR_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.ellipse_parameters.major_radius",
        )
        minor_radius = self.runtime._value_state(
            ops.ellipse_parameters_minor_radius,
            result=SCALAR_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.ellipse_parameters.minor_radius",
        )
        x_direction = self.runtime._value_state(
            ops.ellipse_parameters_x_direction,
            result=VECTOR3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.ellipse_parameters.x_direction",
        )
        y_direction = self.runtime._value_state(
            ops.ellipse_parameters_y_direction,
            result=VECTOR3_SPEC,
            args=(state,),
            operation_id="zencad.typed.curve.ellipse_parameters.y_direction",
        )
        return EllipseParameters(
            Point3._from_state(self.runtime, center),
            Scalar._from_state(self.runtime, major_radius),
            Scalar._from_state(self.runtime, minor_radius),
            Vector3._from_state(self.runtime, x_direction),
            Vector3._from_state(self.runtime, y_direction),
        )

    def lower_distance_parameter(self, point: Point3, /) -> Scalar:
        if not isinstance(point, Point3):
            raise TypeError("lower_distance_parameter expects Point3")
        require_same_runtime(self.runtime, point)
        state = self.runtime._value_state(
            ops.curve_lower_distance_parameter,
            result=SCALAR_SPEC,
            args=(self._state, point._state),
            operation_id="zencad.typed.curve.lower_distance_parameter",
        )
        return Scalar._from_state(self.runtime, state)

    def trimmed_edge(self, start: ScalarInput, end: ScalarInput, /) -> Edge:
        from .curve_constructors import _curve_trimmed_edge

        return _curve_trimmed_edge(self, start, end)

    def uniform(
        self,
        count: int,
        start: ScalarInput | None = None,
        end: ScalarInput | None = None,
        /,
    ) -> list[Scalar]:
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError("uniform sample count must be a positive int")
        if (start is None) != (end is None):
            raise TypeError("uniform start and end must be provided together")
        expression = self.runtime._expression(
            ops.curve_uniform_parameters,
            result=SCALAR_SEQUENCE_SPEC,
            args=(
                self._state,
                count,
                None if start is None else _scalar_state(self.runtime, start),
                None if end is None else _scalar_state(self.runtime, end),
            ),
            operation_id="zencad.typed.curve.uniform",
            cacheable=False,
        )
        parameters = []
        for index in range(count):
            state = self.runtime._value_state(
                ops.scalar_sequence_item,
                result=SCALAR_SPEC,
                args=(expression, index),
                operation_id="zencad.typed.curve.uniform.item",
            )
            parameters.append(Scalar._from_state(self.runtime, state))
        return parameters

    def uniform_points(
        self,
        count: int,
        start: ScalarInput | None = None,
        end: ScalarInput | None = None,
        /,
    ) -> list[Point3]:
        return [self.point(parameter) for parameter in self.uniform(count, start, end)]

    def edge(
        self,
        interval: Interval | tuple[ScalarInput, ScalarInput] | None = None,
        /,
    ) -> Edge:
        from .curve_constructors import make_edge

        return make_edge(self, interval)

    def transform(self, transformation: Transform, /) -> Curve:
        from .curve_constructors import _curve_transform

        return _curve_transform(self, transformation)

    def native(self) -> Geom_Curve:
        """Materialize an independent mutable OCP curve snapshot."""
        return ops.curve_to_ocp(self._resolved())

    def unlazy(self) -> Curve:
        super().unlazy()
        return self

    def Curve(self) -> Geom_Curve:
        return self.native()

    def AdaptorCurve(self) -> GeomAdaptor_Curve:
        return GeomAdaptor_Curve(self.native())

    def HCurveAdaptor(self) -> GeomAdaptor_Curve:
        return self.AdaptorCurve()


class Curve2(Handle[ops.Curve2Value]):
    """Stable two-dimensional curve backed by a snapshot or expression."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ops.Curve2Value]] = CURVE2_SPEC

    @classmethod
    def _from_state(
        cls: type[Curve2HandleT],
        runtime: Runtime,
        state: State[ops.Curve2Value],
    ) -> Curve2HandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.curve2.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_ocp(
        cls: type[Curve2HandleT],
        value: Geom2d_Curve,
        *,
        runtime: Runtime,
    ) -> Curve2HandleT:
        """Copy a mutable OCP curve into an immutable typed snapshot."""
        return cls._from_state(runtime, ops.curve2_from_ocp(value))

    def point(self, parameter: ScalarInput, /) -> Point2:
        state = self.runtime._value_state(
            ops.curve2_point,
            result=POINT2_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.curve2.point",
        )
        return Point2._from_state(self.runtime, state)

    def tangent(self, parameter: ScalarInput, /) -> Vector2:
        """Return the first derivative vector at ``parameter``."""
        state = self.runtime._value_state(
            ops.curve2_tangent,
            result=VECTOR2_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.curve2.tangent",
        )
        return Vector2._from_state(self.runtime, state)

    def range(self) -> Interval:
        first = self.runtime._value_state(
            ops.curve2_first_parameter,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve2.first_parameter",
        )
        last = self.runtime._value_state(
            ops.curve2_last_parameter,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.curve2.last_parameter",
        )
        return Interval(
            Scalar._from_state(self.runtime, first),
            Scalar._from_state(self.runtime, last),
        )

    def trim(self, start: ScalarInput, end: ScalarInput, /) -> Curve2:
        from .curve_constructors import trim_curve2

        return trim_curve2(self, start, end)

    def rotate(self, angle: ScalarInput, /) -> Curve2:
        from .curve_constructors import _curve2_rotate

        return _curve2_rotate(self, angle)

    def native(self) -> Geom2d_Curve:
        """Materialize an independent mutable OCP curve snapshot."""
        return ops.curve2_to_ocp(self._resolved())

    def unlazy(self) -> Curve2:
        super().unlazy()
        return self
