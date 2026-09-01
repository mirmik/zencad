"""Typed topology sweep operations declared at module level."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Literal, overload

from evalcache import ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.operation import (
    OperationArguments,
    arguments,
    operation,
    resolve_runtime,
    using_runtime,
)

from . import _operations as ops
from ._core import State
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
from .values import (
    Scalar,
    ScalarInput,
    Vector3,
    _optional_scalar_state,
    _scalar_state,
    vector3,
)

if TYPE_CHECKING:
    from .runtime import Runtime


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
    backend=ops.extrude_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.extrude",
    operation_version="1",
)
def extrude(
    shape: Shape,
    vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
    center: bool = False,
) -> OperationArguments:
    _require_shape(shape, "extrude")
    _require_bool(center, "extrude center")
    runtime = resolve_runtime(shape, vec)
    with using_runtime(runtime):
        resolved_vector = (
            vector3(0, 0, vec)
            if isinstance(vec, (Scalar, int, float)) and not isinstance(vec, bool)
            else vector3(vec)
        )
    return arguments(shape, resolved_vector, center)


def linear_extrude(
    shape: Shape,
    vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
    center: bool = False,
) -> Shape:
    """Compatibility spelling for :func:`extrude`."""

    return extrude(shape, vec, center)


@operation(
    backend=ops.revolve_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.revol",
    operation_version="1",
)
def revol(
    shape: Shape,
    r: ScalarInput | None = None,
    yaw: ScalarInput = 0,
) -> OperationArguments:
    _require_shape(shape, "revol")
    runtime = resolve_runtime(shape, r, yaw)
    return arguments(
        shape,
        _optional_scalar_state(runtime, r),
        _scalar_state(runtime, yaw),
    )


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
    backend=ops.loft_shapes,
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
    max_degree: int = 4,
) -> OperationArguments:
    _require_bool(smooth, "loft smooth")
    _require_bool(shell, "loft shell")
    values = _require_wire_parts(sections, "loft")
    if len(values) < 2:
        raise ValueError("loft requires at least two sections")
    return arguments(
        values,
        smooth,
        shell,
        _require_positive_int(max_degree, "loft max_degree"),
    )


@operation(
    backend=ops.pipe_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.pipe",
    operation_version="1",
)
def pipe(
    profile: Shape,
    spine: Edge | Wire,
    /,
    *,
    trihedron: PipeTrihedron = PipeTrihedron.CORRECTED_FRENET,
    force_approx_c1: bool = False,
) -> OperationArguments:
    _require_shape(profile, "pipe profile")
    _require_pipe_spine(spine, "pipe spine")
    if not isinstance(trihedron, PipeTrihedron):
        raise TypeError("pipe trihedron must be PipeTrihedron")
    _require_bool(force_approx_c1, "pipe force_approx_c1")
    return arguments(profile, spine, trihedron.value, force_approx_c1)


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
    profiles: Sequence[Edge | Wire],
    spine: Edge | Wire,
    /,
    *,
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
    profiles: Sequence[Edge | Wire],
    spine: Edge | Wire,
    /,
    *,
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
    backend=ops.pipe_shell_shapes,
    result=SOLID_SPEC,
    returns=_pipe_shell_result_type,
    select_result=_pipe_shell_result_spec,
    operation_id="zencad.typed.pipe_shell",
    operation_version="1",
)
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
) -> OperationArguments:
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
    resolve_runtime(values, spine, binormal, parallel)
    return arguments(
        values,
        spine,
        frenet,
        approx_c1,
        binormal,
        parallel,
        discrete,
        solid,
        transition.value,
    )


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
    backend=ops.revolve_sections_shape,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.revol2",
    operation_version="1",
)
def revol2(
    profile: Shape,
    radius: ScalarInput,
    /,
    *,
    sections: int = 30,
    yaw: Interval | Sequence[ScalarInput] = (0, 2 * math.pi),
    roll: Interval | Sequence[ScalarInput] = (0, 0),
    parts: int | None = None,
) -> OperationArguments:
    _require_shape(profile, "revol2 profile")
    resolved_sections = _require_positive_int(sections, "revol2 sections")
    if resolved_sections < 2:
        raise ValueError("revol2 sections must be at least two")
    resolved_parts = None
    if parts is not None:
        resolved_parts = _require_positive_int(parts, "revol2 parts")
        if resolved_sections < resolved_parts * 2:
            raise ValueError("revol2 sections must provide at least two per part")
    runtime = resolve_runtime(profile, radius, yaw, roll)
    return arguments(
        profile,
        _scalar_state(runtime, radius),
        resolved_sections,
        _interval_state(runtime, yaw, "revol2 yaw"),
        _interval_state(runtime, roll, "revol2 roll"),
        resolved_parts,
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
    resolve_runtime(values)
    return values


def _interval_state(
    runtime: Runtime,
    interval: Interval | Sequence[ScalarInput],
    name: str,
) -> tuple[State[float], State[float]]:
    if isinstance(interval, Interval):
        return (interval.lower._state, interval.upper._state)
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence):
        raise TypeError(f"{name} must contain two scalar bounds")
    values = tuple(interval)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    return (_scalar_state(runtime, values[0]), _scalar_state(runtime, values[1]))


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
