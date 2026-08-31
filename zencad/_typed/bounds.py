"""Typed immutable boundary-box handle and materialized record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeVar

from OCP.Bnd import Bnd_Box
from evalcache import Expression, ResultSpec

from . import _bound_operations as ops
from ._core import Handle, State, require_same_runtime
from ._serialization import BoundaryBoxSerializer
from .records import Interval
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR3_SPEC,
    Point3,
    Scalar,
    Vector3,
)

if TYPE_CHECKING:
    from .runtime import Runtime
    from .topology import Solid


BoundaryBoxHandleT = TypeVar("BoundaryBoxHandleT", bound="BoundaryBox")


@dataclass(frozen=True, slots=True)
class BoundaryBoxRecord:
    """Materialized Python representation of a non-empty boundary box."""

    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float

    @property
    def minimum(self) -> tuple[float, float, float]:
        return (self.xmin, self.ymin, self.zmin)

    @property
    def maximum(self) -> tuple[float, float, float]:
        return (self.xmax, self.ymax, self.zmax)


_BOUNDARY_BOX_SERIALIZER = BoundaryBoxSerializer()
BOUNDARY_BOX_SPEC = ResultSpec.for_type(
    ops.BoundaryBoxValue,
    type_id="zencad.typed.BoundaryBox.v1",
    serializer=_BOUNDARY_BOX_SERIALIZER,
    validator=ops.valid_boundary_box,
)


class BoundaryBox(Handle[ops.BoundaryBoxValue]):
    """Stable empty-or-bounded axis-aligned box with a hidden graph."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ops.BoundaryBoxValue]] = BOUNDARY_BOX_SPEC

    @classmethod
    def _from_state(
        cls: type[BoundaryBoxHandleT],
        runtime: Runtime,
        state: State[ops.BoundaryBoxValue],
    ) -> BoundaryBoxHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.boundary-box.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_ocp(
        cls: type[BoundaryBoxHandleT],
        value: Bnd_Box,
        *,
        runtime: Runtime,
    ) -> BoundaryBoxHandleT:
        """Copy a mutable OCP boundary box into an immutable typed value."""
        return cls._from_state(runtime, ops.boundary_box_from_ocp(value))

    def union(self, other: BoundaryBox, /) -> BoundaryBox:
        if not isinstance(other, BoundaryBox):
            raise TypeError("BoundaryBox.union expects BoundaryBox")
        require_same_runtime(self.runtime, other)
        state = self.runtime._value_state(
            ops.boundary_box_union,
            result=BOUNDARY_BOX_SPEC,
            args=(self._state, other._state),
            operation_id="zencad.typed.boundary-box.union",
        )
        return BoundaryBox._from_state(self.runtime, state)

    def add(self, other: BoundaryBox, /) -> BoundaryBox:
        """Immutable compatibility spelling: return the combined box."""
        return self.union(other)

    def is_empty(self) -> bool:
        """Materialize the box because Python control flow needs a bool."""
        return self._resolved().is_empty

    def _coordinate(self, index: int) -> Scalar:
        state = self.runtime._value_state(
            ops.boundary_box_coordinate,
            result=SCALAR_SPEC,
            args=(self._state, index),
            operation_id="zencad.typed.boundary-box.coordinate",
        )
        return Scalar._from_state(self.runtime, state)

    @property
    def xmin(self) -> Scalar:
        return self._coordinate(0)

    @property
    def xmax(self) -> Scalar:
        return self._coordinate(1)

    @property
    def ymin(self) -> Scalar:
        return self._coordinate(2)

    @property
    def ymax(self) -> Scalar:
        return self._coordinate(3)

    @property
    def zmin(self) -> Scalar:
        return self._coordinate(4)

    @property
    def zmax(self) -> Scalar:
        return self._coordinate(5)

    @property
    def minimum(self) -> Point3:
        state = self.runtime._value_state(
            ops.boundary_box_point,
            result=POINT3_SPEC,
            args=(self._state, False),
            operation_id="zencad.typed.boundary-box.minimum",
        )
        return Point3._from_state(self.runtime, state)

    @property
    def maximum(self) -> Point3:
        state = self.runtime._value_state(
            ops.boundary_box_point,
            result=POINT3_SPEC,
            args=(self._state, True),
            operation_id="zencad.typed.boundary-box.maximum",
        )
        return Point3._from_state(self.runtime, state)

    @property
    def size(self) -> Vector3:
        state = self.runtime._value_state(
            ops.boundary_box_size,
            result=VECTOR3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.boundary-box.size",
        )
        return Vector3._from_state(self.runtime, state)

    @property
    def center(self) -> Point3:
        state = self.runtime._value_state(
            ops.boundary_box_center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.boundary-box.center",
        )
        return Point3._from_state(self.runtime, state)

    def x_range(self) -> Interval:
        return Interval(self.xmin, self.xmax)

    def xrange(self) -> Interval:
        return self.x_range()

    def y_range(self) -> Interval:
        return Interval(self.ymin, self.ymax)

    def yrange(self) -> Interval:
        return self.y_range()

    def z_range(self) -> Interval:
        return Interval(self.zmin, self.zmax)

    def zrange(self) -> Interval:
        return self.z_range()

    def xlength(self) -> Scalar:
        return self.size.x

    def ylength(self) -> Scalar:
        return self.size.y

    def zlength(self) -> Scalar:
        return self.size.z

    def shape(self) -> Solid:
        """Return a graph-preserving Solid occupying these bounds."""
        return self.runtime.box(self.size).move(self.minimum)

    def value(self) -> BoundaryBoxRecord:
        resolved = self._resolved()
        if resolved.coordinates is None:
            raise ValueError("empty BoundaryBox has no materialized record")
        return BoundaryBoxRecord(*resolved.coordinates)

    def native(self) -> Bnd_Box:
        """Materialize an independent mutable OCP boundary box."""
        return ops.boundary_box_to_ocp(self._resolved())

    def unlazy(self) -> BoundaryBox:
        super().unlazy()
        return self
