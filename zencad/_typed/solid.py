"""Typed solid primitives declared as module-level domain operations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from zencad.operation import OperationArguments, arguments, operation, resolve_runtime

from . import _operations as ops
from ._core import require_same_runtime
from .topology import SOLID_SPEC, Solid
from .values import ScalarInput, Vector3

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


def _require_center(
    value: bool | str | None,
    name: str,
) -> bool | str | None:
    if value is not None and not isinstance(value, (bool, str)):
        raise TypeError(f"{name} must be bool, str, or None")
    return value


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
        return runtime.vector(values[0], values[1], values[2])
    scalar = cast(ScalarInput, source)
    if y is None and z is None:
        return runtime.vector(scalar, scalar, scalar)
    if y is not None and z is not None:
        return runtime.vector(scalar, y, z)
    raise TypeError("box expects one size or all three dimensions")


__all__ = ["box"]
