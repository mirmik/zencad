"""Typed surface handles containing ZenCad's evaluation graph."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, ClassVar, TypeVar

from OCP.Geom import Geom_Surface
from evalcache.v2 import Expression, ResultSpec

from . import _surface_operations as ops
from ._core import Handle, State, require_same_runtime
from ._serialization import SurfaceSerializer
from .curves import CURVE_SPEC, Curve, Curve2
from .records import Interval
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR3_SPEC,
    Point3,
    Scalar,
    ScalarInput,
    Vector3,
    _scalar_state,
)

if TYPE_CHECKING:
    from .runtime import Runtime
    from .topology import Edge


SurfaceHandleT = TypeVar("SurfaceHandleT", bound="Surface")


class SweepTrihedron(Enum):
    """Supported explicit trihedron laws for the representative sweep."""

    CORRECTED_FRENET = "corrected_frenet"
    FRENET = "frenet"


_SURFACE_SERIALIZER = SurfaceSerializer()
SURFACE_SPEC = ResultSpec.for_type(
    ops.SurfaceValue,
    type_id="zencad.typed.Surface.v1",
    serializer=_SURFACE_SERIALIZER,
    validator=ops.valid_surface,
)


class Surface(Handle[ops.SurfaceValue]):
    """Stable parametric surface backed by a snapshot or expression."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ops.SurfaceValue]] = SURFACE_SPEC

    @classmethod
    def _from_state(
        cls: type[SurfaceHandleT],
        runtime: Runtime,
        state: State[ops.SurfaceValue],
    ) -> SurfaceHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.surface.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_ocp(
        cls: type[SurfaceHandleT],
        value: Geom_Surface,
        *,
        runtime: Runtime,
    ) -> SurfaceHandleT:
        """Copy a mutable OCP surface into an immutable typed snapshot."""
        return cls._from_state(runtime, ops.surface_from_ocp(value))

    def point(self, u: ScalarInput, v: ScalarInput, /) -> Point3:
        state = self.runtime._value_state(
            ops.surface_point,
            result=POINT3_SPEC,
            args=(
                self._state,
                _scalar_state(self.runtime, u),
                _scalar_state(self.runtime, v),
            ),
            operation_id="zencad.typed.surface.point",
        )
        return Point3._from_state(self.runtime, state)

    def normal(self, u: ScalarInput, v: ScalarInput, /) -> Vector3:
        state = self.runtime._value_state(
            ops.surface_normal,
            result=VECTOR3_SPEC,
            args=(
                self._state,
                _scalar_state(self.runtime, u),
                _scalar_state(self.runtime, v),
            ),
            operation_id="zencad.typed.surface.normal",
        )
        return Vector3._from_state(self.runtime, state)

    def _range(self, first_index: int, name: str) -> Interval:
        first = self.runtime._value_state(
            ops.surface_bound,
            result=SCALAR_SPEC,
            args=(self._state, first_index),
            operation_id=f"zencad.typed.surface.{name}.first",
        )
        last = self.runtime._value_state(
            ops.surface_bound,
            result=SCALAR_SPEC,
            args=(self._state, first_index + 1),
            operation_id=f"zencad.typed.surface.{name}.last",
        )
        return Interval(
            Scalar._from_state(self.runtime, first),
            Scalar._from_state(self.runtime, last),
        )

    def u_range(self) -> Interval:
        return self._range(0, "u_range")

    def v_range(self) -> Interval:
        return self._range(2, "v_range")

    def u_iso(self, parameter: ScalarInput, /) -> Curve:
        state = self.runtime._value_state(
            ops.surface_u_iso,
            result=CURVE_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.surface.u_iso",
        )
        return Curve._from_state(self.runtime, state)

    def v_iso(self, parameter: ScalarInput, /) -> Curve:
        state = self.runtime._value_state(
            ops.surface_v_iso,
            result=CURVE_SPEC,
            args=(self._state, _scalar_state(self.runtime, parameter)),
            operation_id="zencad.typed.surface.v_iso",
        )
        return Curve._from_state(self.runtime, state)

    def map(self, curve: Curve2, /) -> Edge:
        """Map a parametric 2D curve onto this surface as a topology edge."""
        from . import _operations as topology_ops
        from .topology import EDGE_SPEC, Edge

        if not isinstance(curve, Curve2):
            raise TypeError("Surface.map expects Curve2")
        require_same_runtime(self.runtime, curve)
        expression = self.runtime._expression(
            topology_ops.surface_map_curve2,
            result=EDGE_SPEC,
            args=(self._state, curve._state),
            operation_id="zencad.typed.surface.map",
        )
        return Edge._from_state(self.runtime, expression)

    def native(self) -> Geom_Surface:
        """Materialize an independent mutable OCP surface snapshot."""
        return ops.surface_to_ocp(self._resolved())

    def unlazy(self) -> Surface:
        super().unlazy()
        return self
