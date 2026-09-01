"""Surface/topology bridge operations declared outside domain handles."""

from __future__ import annotations

from zencad.operation import OperationArguments, arguments, operation

from . import _operations as ops
from .curves import Curve2
from .surfaces import SURFACE_SPEC, Surface
from .topology import EDGE_SPEC, Edge, Face


@operation(
    backend=ops.surface_map_curve2,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.surface.map",
    operation_version="1",
)
def _surface_map_curve2(
    surface: Surface,
    curve: Curve2,
    /,
) -> OperationArguments:
    if not isinstance(surface, Surface):
        raise TypeError("Surface.map expects Surface")
    if not isinstance(curve, Curve2):
        raise TypeError("Surface.map expects Curve2")
    return arguments(surface, curve)


@operation(
    backend=ops.face_surface,
    result=SURFACE_SPEC,
    returns=Surface,
    operation_id="zencad.typed.face.surface",
    operation_version="1",
    fold_literals=True,
)
def _face_surface(face: Face, /) -> OperationArguments:
    if not isinstance(face, Face):
        raise TypeError("Face.surface expects Face")
    return arguments(face)


__all__ = []
