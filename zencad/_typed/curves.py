"""Typed 3D and 2D curve handles containing ZenCad's evaluation graph."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeVar

from OCP.Geom import Geom_Curve
from OCP.Geom2d import Geom2d_Curve
from evalcache.v2 import Expression, ResultSpec

from . import _curve_operations as ops
from ._core import Handle, State
from ._serialization import Curve2Serializer, CurveSerializer
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


CurveHandleT = TypeVar("CurveHandleT", bound="Curve")
Curve2HandleT = TypeVar("Curve2HandleT", bound="Curve2")

_CURVE_SERIALIZER = CurveSerializer()
_CURVE2_SERIALIZER = Curve2Serializer()

CURVE_SPEC = ResultSpec.for_type(
    ops.CurveValue,
    type_id="zencad.typed.Curve.v1",
    serializer=_CURVE_SERIALIZER,
    validator=ops.valid_curve,
)
CURVE2_SPEC = ResultSpec.for_type(
    ops.Curve2Value,
    type_id="zencad.typed.Curve2.v1",
    serializer=_CURVE2_SERIALIZER,
    validator=ops.valid_curve2,
)


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

    def tangent(self, parameter: ScalarInput, /) -> Vector3:
        """Return the first derivative vector at ``parameter``."""
        state = self.runtime._value_state(
            ops.curve_tangent,
            result=VECTOR3_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.curve.tangent",
        )
        return Vector3._from_state(self.runtime, state)

    def range(self) -> tuple[Scalar, Scalar]:
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
        return (
            Scalar._from_state(self.runtime, first),
            Scalar._from_state(self.runtime, last),
        )

    def native(self) -> Geom_Curve:
        """Materialize an independent mutable OCP curve snapshot."""
        return ops.curve_to_ocp(self._resolved())

    def unlazy(self) -> Curve:
        super().unlazy()
        return self


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

    def range(self) -> tuple[Scalar, Scalar]:
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
        return (
            Scalar._from_state(self.runtime, first),
            Scalar._from_state(self.runtime, last),
        )

    def trim(self, start: ScalarInput, end: ScalarInput, /) -> Curve2:
        return self.runtime.trim_curve2(self, start, end)

    def native(self) -> Geom2d_Curve:
        """Materialize an independent mutable OCP curve snapshot."""
        return ops.curve2_to_ocp(self._resolved())

    def unlazy(self) -> Curve2:
        super().unlazy()
        return self
