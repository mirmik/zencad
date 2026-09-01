"""Typed immutable boundary-box handle and materialized record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeVar

from evalcache import Expression, ResultSpec
from OCP.Bnd import Bnd_Box

from zencad.operation import (
    operation,
    using_context,
)

from . import _bound_operations as ops
from ._core import Handle, State
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
    from .context import Context
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

    def __init__(
        self,
        value: ops.BoundaryBoxValue,
        *,
        context: Context | None = None,
    ) -> None:
        from zencad.operation import execution_context

        selected_context = execution_context() if context is None else context
        self._bind(
            selected_context,
            self._result_spec.validate(value, "zencad.typed.boundary-box.construct"),
        )

    @classmethod
    def _from_state(
        cls: type[BoundaryBoxHandleT],
        context: Context,
        state: State[ops.BoundaryBoxValue],
    ) -> BoundaryBoxHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.boundary-box.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def from_ocp(
        cls: type[BoundaryBoxHandleT],
        value: Bnd_Box,
        *,
        context: Context,
    ) -> BoundaryBoxHandleT:
        """Copy a mutable OCP boundary box into an immutable typed value."""
        return cls._from_state(context, ops.boundary_box_from_ocp(value))

    def union(self, other: BoundaryBox, /) -> BoundaryBox:
        return _boundary_box_union(self, other)

    def add(self, other: BoundaryBox, /) -> BoundaryBox:
        """Immutable compatibility spelling: return the combined box."""
        return self.union(other)

    def is_empty(self) -> bool:
        """Materialize the box because Python control flow needs a bool."""
        return self._resolved().is_empty

    def _coordinate(self, index: int) -> Scalar:
        return _boundary_box_coordinate(self, index)

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
        return _boundary_box_minimum(self)

    @property
    def maximum(self) -> Point3:
        return _boundary_box_maximum(self)

    @property
    def size(self) -> Vector3:
        return _boundary_box_size(self)

    @property
    def center(self) -> Point3:
        return _boundary_box_center(self)

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
        from .solid import box

        with using_context(self.context):
            return box(self.size).move(self.minimum)

    def value(self) -> BoundaryBoxRecord:
        resolved = self._resolved()
        if resolved.coordinates is None:
            raise ValueError("empty BoundaryBox has no materialized record")
        return BoundaryBoxRecord(*resolved.coordinates)

    def native(self) -> Bnd_Box:
        """Materialize an independent mutable OCP boundary box."""
        return ops.boundary_box_to_ocp(self._resolved())


@operation(
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.boundary-box.empty",
    operation_version="1",
    fold_literals=True,
)
def empty_boundary_box() -> BoundaryBox:
    return BoundaryBox(ops.empty_boundary_box())


@operation(
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.boundary-box.from-points",
    operation_version="1",
    fold_literals=True,
)
def boundary_box(minimum: Point3, maximum: Point3, /) -> BoundaryBox:
    if not isinstance(minimum, Point3) or not isinstance(maximum, Point3):
        raise TypeError("boundary_box expects Point3 corners")
    return BoundaryBox(
        ops.boundary_box_from_points(minimum._resolved(), maximum._resolved())
    )


@operation(
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.boundary-box.union",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_union(
    left: BoundaryBox,
    right: BoundaryBox,
    /,
) -> BoundaryBox:
    if not isinstance(left, BoundaryBox) or not isinstance(right, BoundaryBox):
        raise TypeError("BoundaryBox.union expects BoundaryBox")
    return BoundaryBox(ops.boundary_box_union(left._resolved(), right._resolved()))


@operation(
    result=SCALAR_SPEC,
    returns=Scalar,
    operation_id="zencad.typed.boundary-box.coordinate",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_coordinate(
    value: BoundaryBox,
    index: int,
    /,
) -> Scalar:
    if not isinstance(value, BoundaryBox):
        raise TypeError("boundary-box coordinate expects BoundaryBox")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < 6:
        raise ValueError("boundary-box coordinate index must be between 0 and 5")
    return Scalar(ops.boundary_box_coordinate(value._resolved(), index))


@operation(
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.boundary-box.minimum",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_minimum(value: BoundaryBox, /) -> Point3:
    if not isinstance(value, BoundaryBox):
        raise TypeError("boundary-box minimum expects BoundaryBox")
    point = ops.boundary_box_point(value._resolved(), False)
    return Point3(point.x, point.y, point.z)


@operation(
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.boundary-box.maximum",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_maximum(value: BoundaryBox, /) -> Point3:
    if not isinstance(value, BoundaryBox):
        raise TypeError("boundary-box maximum expects BoundaryBox")
    point = ops.boundary_box_point(value._resolved(), True)
    return Point3(point.x, point.y, point.z)


@operation(
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.boundary-box.size",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_size(value: BoundaryBox, /) -> Vector3:
    if not isinstance(value, BoundaryBox):
        raise TypeError("boundary-box size expects BoundaryBox")
    vector = ops.boundary_box_size(value._resolved())
    return Vector3(vector.x, vector.y, vector.z)


@operation(
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.boundary-box.center",
    operation_version="1",
    fold_literals=True,
)
def _boundary_box_center(value: BoundaryBox, /) -> Point3:
    if not isinstance(value, BoundaryBox):
        raise TypeError("boundary-box center expects BoundaryBox")
    point = ops.boundary_box_center(value._resolved())
    return Point3(point.x, point.y, point.z)


__all__ = [
    "BoundaryBox",
    "BoundaryBoxRecord",
    "boundary_box",
    "empty_boundary_box",
]
