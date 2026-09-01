"""Typed surface handles containing ZenCad's evaluation graph."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, TypeVar

from evalcache import Expression, ResultSpec
from OCP.Geom import Geom_Surface

from zencad.operation import OperationArguments, arguments, operation, resolve_runtime

from . import _surface_operations as ops
from ._core import Handle, State, require_same_runtime
from ._serialization import SurfaceSerializer
from .curves import CURVE_SPEC, Curve, Curve2
from .records import Interval
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    VECTOR3_SPEC,
    Number,
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
    """Supported immutable trihedron laws for a sweep location."""

    CORRECTED_FRENET = "corrected_frenet"
    FRENET = "frenet"


@dataclass(frozen=True, slots=True)
class SweepScaleLaw:
    """Constant scale over an explicit parametric domain."""

    scale: Scalar
    domain: Interval

    def __post_init__(self) -> None:
        if not isinstance(self.scale, Scalar):
            raise TypeError("SweepScaleLaw scale must be Scalar")
        if not isinstance(self.domain, Interval):
            raise TypeError("SweepScaleLaw domain must be Interval")
        require_same_runtime(self.scale.runtime, self.domain.lower)
        require_same_runtime(self.scale.runtime, self.domain.upper)

    @property
    def runtime(self) -> Runtime:
        return self.scale.runtime

    def unlazy(self) -> SweepScaleLaw:
        self.scale.unlazy()
        self.domain.unlazy()
        return self


@dataclass(frozen=True, slots=True)
class SweepSectionLaw:
    """A section curve evolved by a typed scale law."""

    section: Curve
    scale: SweepScaleLaw

    def __post_init__(self) -> None:
        if not isinstance(self.section, Curve):
            raise TypeError("SweepSectionLaw section must be Curve")
        if not isinstance(self.scale, SweepScaleLaw):
            raise TypeError("SweepSectionLaw scale must be SweepScaleLaw")
        require_same_runtime(self.section.runtime, self.scale.scale)

    @property
    def runtime(self) -> Runtime:
        return self.section.runtime

    def unlazy(self) -> SweepSectionLaw:
        self.section.unlazy()
        self.scale.unlazy()
        return self


@dataclass(frozen=True, slots=True)
class SweepLocationLaw:
    """A spine curve paired with an explicit trihedron law."""

    spine: Curve
    trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET

    def __post_init__(self) -> None:
        if not isinstance(self.spine, Curve):
            raise TypeError("SweepLocationLaw spine must be Curve")
        if not isinstance(self.trihedron, SweepTrihedron):
            raise TypeError("SweepLocationLaw trihedron must be SweepTrihedron")

    @property
    def runtime(self) -> Runtime:
        return self.spine.runtime

    def unlazy(self) -> SweepLocationLaw:
        self.spine.unlazy()
        return self


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
        return _surface_point(self, u, v)

    def normal(self, u: ScalarInput, v: ScalarInput, /) -> Vector3:
        return _surface_normal(self, u, v)

    def u_range(self) -> Interval:
        return Interval(_surface_u_first(self), _surface_u_last(self))

    def v_range(self) -> Interval:
        return Interval(_surface_v_first(self), _surface_v_last(self))

    def u_iso(self, parameter: ScalarInput, /) -> Curve:
        return _surface_u_iso(self, parameter)

    def v_iso(self, parameter: ScalarInput, /) -> Curve:
        return _surface_v_iso(self, parameter)

    def map(self, curve: Curve2, /) -> Edge:
        """Map a parametric 2D curve onto this surface as a topology edge."""
        from .surface_topology import _surface_map_curve2

        return _surface_map_curve2(self, curve)

    def native(self) -> Geom_Surface:
        """Materialize an independent mutable OCP surface snapshot."""
        return ops.surface_to_ocp(self._resolved())

    def unlazy(self) -> Surface:
        super().unlazy()
        return self


@operation(
    backend=ops.cylinder_surface,
    result=SURFACE_SPEC,
    returns=Surface,
    operation_id="zencad.typed.cylinder_surface",
    operation_version="1",
)
def cylinder_surface(radius: ScalarInput, /) -> OperationArguments:
    runtime = resolve_runtime(radius)
    return arguments(_scalar_state(runtime, radius))


@operation(
    backend=ops.surface_point,
    result=POINT3_SPEC,
    returns=Point3,
    operation_id="zencad.typed.surface.point",
    operation_version="1",
    fold_literals=True,
)
def _surface_point(
    surface: Surface,
    u: ScalarInput,
    v: ScalarInput,
    /,
) -> OperationArguments:
    if not isinstance(surface, Surface):
        raise TypeError("surface point expects Surface")
    runtime = resolve_runtime(surface, u, v)
    return arguments(
        surface,
        _scalar_state(runtime, u),
        _scalar_state(runtime, v),
    )


@operation(
    backend=ops.surface_normal,
    result=VECTOR3_SPEC,
    returns=Vector3,
    operation_id="zencad.typed.surface.normal",
    operation_version="1",
    fold_literals=True,
)
def _surface_normal(
    surface: Surface,
    u: ScalarInput,
    v: ScalarInput,
    /,
) -> OperationArguments:
    if not isinstance(surface, Surface):
        raise TypeError("surface normal expects Surface")
    runtime = resolve_runtime(surface, u, v)
    return arguments(
        surface,
        _scalar_state(runtime, u),
        _scalar_state(runtime, v),
    )


def _surface_bound_operation(operation_id: str, index: int):
    @operation(
        backend=ops.surface_bound,
        result=SCALAR_SPEC,
        returns=Scalar,
        operation_id=operation_id,
        operation_version="1",
        fold_literals=True,
    )
    def bound(surface: Surface, /) -> OperationArguments:
        if not isinstance(surface, Surface):
            raise TypeError("surface bound expects Surface")
        return arguments(surface, index)

    return bound


_surface_u_first = _surface_bound_operation(
    "zencad.typed.surface.u_range.first", 0
)
_surface_u_last = _surface_bound_operation(
    "zencad.typed.surface.u_range.last", 1
)
_surface_v_first = _surface_bound_operation(
    "zencad.typed.surface.v_range.first", 2
)
_surface_v_last = _surface_bound_operation(
    "zencad.typed.surface.v_range.last", 3
)


@operation(
    backend=ops.surface_u_iso,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.surface.u_iso",
    operation_version="1",
    fold_literals=True,
)
def _surface_u_iso(
    surface: Surface,
    parameter: ScalarInput,
    /,
) -> OperationArguments:
    if not isinstance(surface, Surface):
        raise TypeError("surface u_iso expects Surface")
    runtime = resolve_runtime(surface, parameter)
    return arguments(surface, _scalar_state(runtime, parameter))


@operation(
    backend=ops.surface_v_iso,
    result=CURVE_SPEC,
    returns=Curve,
    operation_id="zencad.typed.surface.v_iso",
    operation_version="1",
    fold_literals=True,
)
def _surface_v_iso(
    surface: Surface,
    parameter: ScalarInput,
    /,
) -> OperationArguments:
    if not isinstance(surface, Surface):
        raise TypeError("surface v_iso expects Surface")
    runtime = resolve_runtime(surface, parameter)
    return arguments(surface, _scalar_state(runtime, parameter))


def constant_sweep_scale(
    scale: ScalarInput,
    domain: Interval,
    /,
) -> SweepScaleLaw:
    """Describe a constant sweep scale over an explicit domain."""

    if not isinstance(domain, Interval):
        raise TypeError("constant_sweep_scale domain must be Interval")
    runtime = resolve_runtime(scale, domain.lower, domain.upper)
    return SweepScaleLaw(
        Scalar._from_state(runtime, _scalar_state(runtime, scale)),
        domain,
    )


def evolved_sweep_section(
    section: Curve,
    scale: SweepScaleLaw,
    /,
) -> SweepSectionLaw:
    """Describe a curve section evolved by a scale law."""

    if not isinstance(section, Curve):
        raise TypeError("evolved_sweep_section section must be Curve")
    if not isinstance(scale, SweepScaleLaw):
        raise TypeError("evolved_sweep_section scale must be SweepScaleLaw")
    require_same_runtime(scale.runtime, section)
    return SweepSectionLaw(section, scale)


def sweep_location(
    spine: Curve,
    trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET,
    /,
) -> SweepLocationLaw:
    """Describe a spine location using an explicit trihedron law."""

    if not isinstance(spine, Curve):
        raise TypeError("sweep_location spine must be Curve")
    if not isinstance(trihedron, SweepTrihedron):
        raise TypeError("sweep_location trihedron must be SweepTrihedron")
    return SweepLocationLaw(spine, trihedron)


@operation(
    backend=ops.sweep_surface,
    result=SURFACE_SPEC,
    returns=Surface,
    operation_id="zencad.typed.sweep_surface_from_laws",
    operation_version="1",
)
def sweep_surface_from_laws(
    section: SweepSectionLaw,
    location: SweepLocationLaw,
    /,
    *,
    tolerance: Number = 1e-6,
    continuity: int = 2,
    max_degree: int = 5,
    max_segments: int = 20,
) -> OperationArguments:
    """Build a surface from immutable section and location laws."""

    if not isinstance(section, SweepSectionLaw):
        raise TypeError("sweep_surface_from_laws section must be SweepSectionLaw")
    if not isinstance(location, SweepLocationLaw):
        raise TypeError("sweep_surface_from_laws location must be SweepLocationLaw")
    if section.runtime is not location.runtime:
        raise ValueError("cannot mix handles from different typed runtimes")
    return arguments(
        section.section,
        section.scale.scale,
        section.scale.domain.lower,
        section.scale.domain.upper,
        location.spine,
        location.trihedron.value,
        _require_positive_number(tolerance, "sweep_surface_from_laws tolerance"),
        _require_int_between(
            continuity,
            "sweep_surface_from_laws continuity",
            minimum=0,
            maximum=3,
        ),
        _require_positive_int(max_degree, "sweep_surface_from_laws max_degree"),
        _require_positive_int(max_segments, "sweep_surface_from_laws max_segments"),
    )


def sweep_surface(
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
    require_same_runtime(section.runtime, spine)
    scale_law = constant_sweep_scale(scale, spine.range())
    section_law = evolved_sweep_section(section, scale_law)
    location_law = sweep_location(spine, trihedron)
    return sweep_surface_from_laws(
        section_law,
        location_law,
        tolerance=tolerance,
        continuity=continuity,
        max_degree=max_degree,
        max_segments=max_segments,
    )


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


__all__ = [
    "Surface",
    "SweepLocationLaw",
    "SweepScaleLaw",
    "SweepSectionLaw",
    "SweepTrihedron",
    "constant_sweep_scale",
    "cylinder_surface",
    "evolved_sweep_section",
    "sweep_location",
    "sweep_surface",
    "sweep_surface_from_laws",
]
