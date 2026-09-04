"""Typed topology sweep operations declared at module level."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Literal, overload

from evalcache import ResultSpec

from zencad._native.shape import Shape as ResolvedShape
from zencad.operation import (
    operation,
    resolve_context,
)

from . import _operations as ops
from .records import Interval
from .topology import (
    SHAPE_SPEC,
    SHELL_SPEC,
    SOLID_SPEC,
    Edge,
    Shape,
    Shell,
    Solid,
    Wire,
)
from .values import Vector3


class PipeTrihedron(Enum):
    """OCCT trihedron modes supported by the pipe builder."""

    CORRECTED_FRENET = "corrected_frenet"
    FIXED = "fixed"
    FRENET = "frenet"
    CONSTANT_NORMAL = "constant_normal"
    DARBOUX = "darboux"
    GUIDE_AC = "guide_ac"
    GUIDE_PLAN = "guide_plan"
    GUIDE_AC_WITH_CONTACT = "guide_ac_with_contact"
    GUIDE_PLAN_WITH_CONTACT = "guide_plan_with_contact"
    DISCRETE = "discrete_trihedron"


class PipeTransition(Enum):
    """Corner transition policy for a multi-section pipe shell."""

    TRANSFORMED = 0
    RIGHT_CORNER = 1
    ROUND_CORNER = 2


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.extrude",
    operation_version="1",
)
def extrude(
    shape: Shape,
    vec: Vector3 | Sequence[float] | float,
    center: bool = False,
) -> Shape:
    _require_shape(shape, "extrude")
    _require_bool(center, "extrude center")
    resolved_vector = (
        Vector3(0, 0, vec)
        if isinstance(vec, (int, float)) and not isinstance(vec, bool)
        else vec
        if isinstance(vec, Vector3)
        else Vector3(tuple(vec))
    )
    return Shape(
        ops.extrude_shape(shape._legacy(), resolved_vector._resolved(), center)
    )


def linear_extrude(
    shape: Shape,
    vec: Vector3 | Sequence[float] | float,
    center: bool = False,
) -> Shape:
    """Compatibility spelling for :func:`extrude`."""

    return extrude(shape, vec, center)


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.revol",
    operation_version="1",
)
def revol(
    shape: Shape,
    r: float | None = None,
    yaw: float = 0,
) -> Shape:
    _require_shape(shape, "revol")
    return Shape(ops.revolve_shape(shape._legacy(), r, yaw))


def _loft_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Solid | Shell]:
    shell = args[2] if len(args) > 2 else kwargs.get("shell", False)
    return Shell if shell is True else Solid


def _loft_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    return SHELL_SPEC if _loft_result_type(args, kwargs) is Shell else SOLID_SPEC


@overload
def loft(
    sections: Sequence[Edge | Wire],
    smooth: bool = False,
    shell: Literal[False] = False,
    max_degree: int = 4,
) -> Solid: ...


@overload
def loft(
    sections: Sequence[Edge | Wire],
    smooth: bool = False,
    *,
    shell: Literal[True],
    max_degree: int = 4,
) -> Shell: ...


@overload
def loft(
    sections: Sequence[Edge | Wire],
    smooth: bool,
    shell: Literal[True],
    max_degree: int = 4,
) -> Shell: ...


@overload
def loft(
    sections: Sequence[Edge | Wire],
    smooth: bool = False,
    shell: bool = False,
    max_degree: int = 4,
) -> Solid | Shell: ...


@operation(
    result=SOLID_SPEC,
    returns=_loft_result_type,
    select_result=_loft_result_spec,
    operation_id="zencad.typed.loft",
    operation_version="1",
)
def loft(
    sections: Sequence[Edge | Wire],
    smooth: bool = False,
    shell: bool = False,
    max_degree: int | None = None,
    *,
    maxdegree: int | None = None,
) -> Solid | Shell:
    if maxdegree is not None:
        if max_degree is not None:
            raise TypeError(
                "loft max_degree and legacy maxdegree cannot both be provided"
            )
        max_degree = maxdegree
    if max_degree is None:
        max_degree = 4
    _require_bool(smooth, "loft smooth")
    _require_bool(shell, "loft shell")
    values = _require_wire_parts(sections, "loft")
    if len(values) < 2:
        raise ValueError("loft requires at least two sections")
    resolved = ops.loft_shapes(
        tuple(value._legacy() for value in values),
        smooth,
        shell,
        _require_positive_int(max_degree, "loft max_degree"),
    )
    return Shell(resolved) if shell else Solid(resolved)


@overload
def pipe(
    profile: Shape,
    spine: Edge | Wire,
    /,
    *,
    trihedron: PipeTrihedron = PipeTrihedron.CORRECTED_FRENET,
    force_approx_c1: bool = False,
) -> Shape: ...


@overload
def pipe(
    *,
    shp: Shape,
    spine: Edge | Wire,
    mode: str | PipeTrihedron | None = None,
    force_approx_c1: bool = False,
) -> Shape: ...


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.pipe",
    operation_version="1",
)
def pipe(
    profile: Shape | None = None,
    /,
    spine: Edge | Wire | None = None,
    *,
    shp: Shape | None = None,
    mode: str | PipeTrihedron | None = None,
    trihedron: PipeTrihedron = PipeTrihedron.CORRECTED_FRENET,
    force_approx_c1: bool = False,
) -> Shape:
    if shp is not None:
        if profile is not None:
            raise TypeError("pipe profile and legacy shp cannot both be provided")
        profile = shp
    if profile is None:
        raise TypeError("pipe requires a profile")
    if spine is None:
        raise TypeError("pipe requires a spine")
    if mode is not None:
        if trihedron is not PipeTrihedron.CORRECTED_FRENET:
            raise TypeError("pipe mode and trihedron cannot both be provided")
        try:
            trihedron = mode if isinstance(mode, PipeTrihedron) else PipeTrihedron(mode)
        except ValueError as exception:
            raise ValueError(f"pipe: undefined mode {mode!r}") from exception
    _require_shape(profile, "pipe profile")
    _require_pipe_spine(spine, "pipe spine")
    if not isinstance(trihedron, PipeTrihedron):
        raise TypeError("pipe trihedron must be PipeTrihedron")
    _require_bool(force_approx_c1, "pipe force_approx_c1")
    return Shape(
        ops.pipe_shape(
            profile._legacy(), spine._legacy(), trihedron.value, force_approx_c1
        )
    )


def _pipe_shell_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Solid | Shell]:
    del args
    return Shell if kwargs.get("solid", True) is False else Solid


def _pipe_shell_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    return SHELL_SPEC if _pipe_shell_result_type(args, kwargs) is Shell else SOLID_SPEC


@overload
def pipe_shell(
    profiles: Sequence[Edge | Wire] | None = None,
    spine: Edge | Wire | None = None,
    *,
    arr: Sequence[Edge | Wire] | None = None,
    frenet: bool = False,
    approx_c1: bool = False,
    binormal: Vector3 | None = None,
    parallel: Vector3 | None = None,
    discrete: bool = False,
    solid: Literal[True] = True,
    transition: PipeTransition = PipeTransition.TRANSFORMED,
) -> Solid: ...


@overload
def pipe_shell(
    profiles: Sequence[Edge | Wire] | None = None,
    spine: Edge | Wire | None = None,
    *,
    arr: Sequence[Edge | Wire] | None = None,
    frenet: bool = False,
    approx_c1: bool = False,
    binormal: Vector3 | None = None,
    parallel: Vector3 | None = None,
    discrete: bool = False,
    solid: Literal[False],
    transition: PipeTransition = PipeTransition.TRANSFORMED,
) -> Shell: ...


@overload
def pipe_shell(
    profiles: Sequence[Edge | Wire],
    spine: Edge | Wire,
    /,
    *,
    frenet: bool = False,
    approx_c1: bool = False,
    binormal: Vector3 | None = None,
    parallel: Vector3 | None = None,
    discrete: bool = False,
    solid: bool = True,
    transition: PipeTransition = PipeTransition.TRANSFORMED,
) -> Solid | Shell: ...


@operation(
    result=SOLID_SPEC,
    returns=_pipe_shell_result_type,
    select_result=_pipe_shell_result_spec,
    operation_id="zencad.typed.pipe_shell",
    operation_version="1",
)
def pipe_shell(
    profiles: Sequence[Edge | Wire] | None = None,
    spine: Edge | Wire | None = None,
    *,
    arr: Sequence[Edge | Wire] | None = None,
    frenet: bool = False,
    approx_c1: bool = False,
    binormal: Vector3 | None = None,
    parallel: Vector3 | None = None,
    discrete: bool = False,
    solid: bool = True,
    transition: PipeTransition = PipeTransition.TRANSFORMED,
) -> Solid | Shell:
    if arr is not None:
        if profiles is not None:
            raise TypeError(
                "pipe_shell profiles and legacy arr cannot both be provided"
            )
        profiles = arr
    if profiles is None:
        raise TypeError("pipe_shell requires profiles (legacy name: arr)")
    if spine is None:
        raise TypeError("pipe_shell requires spine")
    values = _require_wire_parts(profiles, "pipe_shell profiles")
    _require_pipe_spine(spine, "pipe_shell spine")
    for flag, name in (
        (frenet, "pipe_shell frenet"),
        (approx_c1, "pipe_shell approx_c1"),
        (discrete, "pipe_shell discrete"),
        (solid, "pipe_shell solid"),
    ):
        _require_bool(flag, name)
    if not isinstance(transition, PipeTransition):
        raise TypeError("pipe_shell transition must be PipeTransition")
    for vector, name in ((binormal, "binormal"), (parallel, "parallel")):
        if vector is not None and not isinstance(vector, Vector3):
            raise TypeError(f"pipe_shell {name} must be Vector3 or None")
    selected_modes = sum((frenet, binormal is not None, parallel is not None, discrete))
    if selected_modes > 1:
        raise ValueError("pipe_shell orientation modes are mutually exclusive")
    resolved = ops.pipe_shell_shapes(
        tuple(value._legacy() for value in values),
        spine._legacy(),
        frenet,
        approx_c1,
        None if binormal is None else binormal._resolved(),
        None if parallel is None else parallel._resolved(),
        discrete,
        solid,
        transition.value,
    )
    return Solid(resolved) if solid else Shell(resolved)


def sweep(
    profile: Edge | Wire,
    path: Edge | Wire,
    /,
    *,
    frenet: bool = False,
) -> Solid:
    """Compatibility spelling for a single-profile solid pipe shell."""

    return pipe_shell((profile,), path, frenet=frenet)


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.revol2",
    operation_version="1",
)
def revol2(
    profile: Shape | None = None,
    radius: float | None = None,
    *,
    r: float | None = None,
    sections: int | None = None,
    n: int | None = None,
    yaw: Interval | Sequence[float] = (0, 2 * math.pi),
    roll: Interval | Sequence[float] = (0, 0),
    parts: int | None = None,
) -> Solid:
    if profile is None:
        raise TypeError("revol2 requires profile")
    if r is not None:
        if radius is not None:
            raise TypeError("revol2 radius and legacy r cannot both be provided")
        radius = r
    if radius is None:
        raise TypeError("revol2 requires radius (legacy name: r)")
    if n is not None:
        if sections is not None:
            raise TypeError("revol2 sections and legacy n cannot both be provided")
        sections = n
    if sections is None:
        sections = 30
    _require_shape(profile, "revol2 profile")
    resolved_sections = _require_positive_int(sections, "revol2 sections")
    if resolved_sections < 2:
        raise ValueError("revol2 sections must be at least two")
    resolved_parts = None
    if parts is not None:
        resolved_parts = _require_positive_int(parts, "revol2 parts")
        if resolved_sections < resolved_parts * 2:
            raise ValueError("revol2 sections must provide at least two per part")
    return Solid(
        ops.revolve_sections_shape(
            profile._legacy(),
            radius,
            resolved_sections,
            _interval_values(yaw, "revol2 yaw"),
            _interval_values(roll, "revol2 roll"),
            resolved_parts,
        )
    )


def _require_shape(shape: Shape, name: str) -> None:
    if not isinstance(shape, Shape):
        raise TypeError(f"{name} expects Shape")


def _require_pipe_spine(spine: Edge | Wire, name: str) -> None:
    if not isinstance(spine, (Edge, Wire)):
        raise TypeError(f"{name} must be Edge or Wire")


def _require_wire_parts(
    shapes: Sequence[Edge | Wire],
    name: str,
) -> tuple[Edge | Wire, ...]:
    if isinstance(shapes, (str, bytes)) or not isinstance(shapes, Sequence):
        raise TypeError(f"{name} expects Edge or Wire handles")
    values = tuple(shapes)
    if not values:
        raise ValueError(f"{name} requires at least one Edge or Wire")
    if not all(isinstance(shape, (Edge, Wire)) for shape in values):
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    resolve_context(values)
    return values


def _interval_values(
    interval: Interval | Sequence[float],
    name: str,
) -> tuple[float, float]:
    if isinstance(interval, Interval):
        return interval.value()
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence):
        raise TypeError(f"{name} must contain two scalar bounds")
    values = tuple(interval)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    return (values[0], values[1])


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


__all__ = [
    "PipeTransition",
    "PipeTrihedron",
    "extrude",
    "linear_extrude",
    "loft",
    "pipe",
    "pipe_shell",
    "revol",
    "revol2",
    "sweep",
]
