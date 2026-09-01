"""Typed solid primitives declared as module-level domain operations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from zencad.operation import OperationArguments, arguments, operation, resolve_runtime

from . import _solid_operations as ops
from ._core import require_same_runtime
from .topology import SOLID_SPEC, Shell, Solid
from .values import (
    ScalarInput,
    Vector3,
    _angle_state,
    _optional_scalar_state,
    _scalar_state,
    vector,
)

if TYPE_CHECKING:
    from .runtime import Runtime


@operation(
    backend=ops.box,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.box",
    operation_version="1",
)
def box(
    x: ScalarInput | Vector3 | Sequence[ScalarInput] = 0,
    y: ScalarInput | None = None,
    z: ScalarInput | None = None,
    center: bool | str | None = None,
    size: ScalarInput | Vector3 | Sequence[ScalarInput] | None = None,
) -> OperationArguments:
    """Build a typed box through the current or operand-owned evaluator."""

    runtime = resolve_runtime(x, y, z, size)
    resolved_center = _require_center(center, "box center")
    resolved_size = _box_size(runtime, x, y, z, size)
    return arguments(resolved_size, resolved_center)


def cube(
    x: ScalarInput | Vector3 | Sequence[ScalarInput] = 0,
    y: ScalarInput | None = None,
    z: ScalarInput | None = None,
    center: bool | str | None = None,
    size: ScalarInput | Vector3 | Sequence[ScalarInput] | None = None,
) -> Solid:
    """Compatibility alias for :func:`box` with the legacy signature."""

    return box(x, y, z, center, size)


@operation(
    backend=ops.sphere,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.sphere",
    operation_version="1",
)
def sphere(
    r: ScalarInput,
    yaw: ScalarInput | None = None,
    pitch: ScalarInput | Sequence[ScalarInput] | None = None,
) -> OperationArguments:
    runtime = resolve_runtime(r, yaw, pitch)
    return arguments(
        _scalar_state(runtime, r),
        _optional_scalar_state(runtime, yaw),
        _angle_state(runtime, pitch, "sphere pitch"),
    )


@operation(
    backend=ops.cylinder,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.cylinder",
    operation_version="1",
)
def cylinder(
    r: ScalarInput,
    h: ScalarInput,
    yaw: ScalarInput | None = None,
    center: bool = False,
) -> OperationArguments:
    _require_bool(center, "cylinder center")
    runtime = resolve_runtime(r, h, yaw)
    return arguments(
        _scalar_state(runtime, r),
        _scalar_state(runtime, h),
        _optional_scalar_state(runtime, yaw),
        center,
    )


@operation(
    backend=ops.cone,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.cone",
    operation_version="1",
)
def cone(
    r1: ScalarInput,
    r2: ScalarInput,
    h: ScalarInput,
    yaw: ScalarInput | None = None,
    center: bool = False,
) -> OperationArguments:
    _require_bool(center, "cone center")
    runtime = resolve_runtime(r1, r2, h, yaw)
    return arguments(
        _scalar_state(runtime, r1),
        _scalar_state(runtime, r2),
        _scalar_state(runtime, h),
        _optional_scalar_state(runtime, yaw),
        center,
    )


@operation(
    backend=ops.torus,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.torus",
    operation_version="1",
)
def torus(
    r1: ScalarInput,
    r2: ScalarInput,
    yaw: ScalarInput | None = None,
    pitch: ScalarInput | Sequence[ScalarInput] | None = None,
) -> OperationArguments:
    runtime = resolve_runtime(r1, r2, yaw, pitch)
    return arguments(
        _scalar_state(runtime, r1),
        _scalar_state(runtime, r2),
        _optional_scalar_state(runtime, yaw),
        _angle_state(runtime, pitch, "torus pitch"),
    )


@operation(
    backend=ops.halfspace,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.halfspace",
    operation_version="1",
)
def halfspace() -> OperationArguments:
    return arguments()


@operation(
    backend=ops.make_solid,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.make_solid",
    operation_version="1",
)
def make_solid(shells: Shell | Sequence[Shell], /) -> OperationArguments:
    return arguments(_require_shells(shells, "make_solid"))


def _require_center(
    value: bool | str | None,
    name: str,
) -> bool | str | None:
    if value is not None and not isinstance(value, (bool, str)):
        raise TypeError(f"{name} must be bool, str, or None")
    return value


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_shells(
    shells: Shell | Sequence[Shell],
    name: str,
) -> tuple[Shell, ...]:
    values: tuple[Shell, ...]
    if isinstance(shells, Shell):
        values = (shells,)
    elif isinstance(shells, Sequence) and not isinstance(shells, (str, bytes)):
        values = tuple(shells)
    else:
        raise TypeError(f"{name} expects Shell or a sequence of Shell")
    if not values:
        raise ValueError(f"{name} requires at least one Shell")
    if not all(isinstance(shell, Shell) for shell in values):
        raise TypeError(f"{name} expects only Shell values")
    return values


def _box_size(
    runtime: Runtime,
    x: ScalarInput | Vector3 | Sequence[ScalarInput],
    y: ScalarInput | None,
    z: ScalarInput | None,
    size: ScalarInput | Vector3 | Sequence[ScalarInput] | None,
) -> Vector3:
    source = x if size is None else size
    if size is not None:
        y = None
        z = None
    if isinstance(source, Vector3):
        if y is not None or z is not None:
            raise TypeError("box Vector3 size cannot be combined with y or z")
        require_same_runtime(runtime, source)
        return source
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
        if y is not None or z is not None:
            raise TypeError("box sequence size cannot be combined with y or z")
        values = tuple(source)
        if len(values) != 3:
            raise TypeError("box size must contain exactly three dimensions")
        return vector(values[0], values[1], values[2])
    scalar = cast(ScalarInput, source)
    if y is None and z is None:
        return vector(scalar, scalar, scalar)
    if y is not None and z is not None:
        return vector(scalar, y, z)
    raise TypeError("box expects one size or all three dimensions")


__all__ = [
    "box",
    "cone",
    "cube",
    "cylinder",
    "halfspace",
    "make_solid",
    "sphere",
    "torus",
]
