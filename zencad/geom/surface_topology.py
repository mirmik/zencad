"""Surface/topology bridge operations declared outside domain handles."""

from __future__ import annotations

from zencad.operation import operation

from . import _operations as ops
from .curves import Curve2
from .surfaces import SURFACE_SPEC, Surface
from .topology import EDGE_SPEC, Edge, Face


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.surface.map",
    operation_version="1",
)
def _surface_map_curve2(
    surface: Surface,
    curve: Curve2,
    /,
) -> Edge:
    if not isinstance(surface, Surface):
        raise TypeError("Surface.map expects Surface")
    if not isinstance(curve, Curve2):
        raise TypeError("Surface.map expects Curve2")
    return Edge(ops.surface_map_curve2(surface._resolved(), curve._resolved()))


@operation(
    result=SURFACE_SPEC,
    returns=Surface,
    operation_id="zencad.typed.face.surface",
    operation_version="1",
    fold_literals=True,
)
def _face_surface(face: Face, /) -> Surface:
    if not isinstance(face, Face):
        raise TypeError("Face.surface expects Face")
    return Surface(ops.face_surface(face._legacy()))


__all__ = []
