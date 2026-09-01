"""Typed immutable indexed-mesh handle and explicit materialization records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, ClassVar, TypeVar

import numpy as np
from OCP.Poly import Poly_Triangulation
from evalcache import Expression, ResultSpec

from zencad.operation import OperationArguments, arguments, operation

from . import _mesh_operations as ops
from ._core import Handle, State
from ._serialization import MeshSerializer
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .values import Number

if TYPE_CHECKING:
    from .context import Context
    from .topology import Face, Shape


MeshHandleT = TypeVar("MeshHandleT", bound="MeshData")
VectorRow = tuple[float, float, float]
TriangleRow = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class MeshDataRecord:
    positions: tuple[VectorRow, ...]
    normals: tuple[VectorRow, ...]
    triangles: tuple[TriangleRow, ...]
    triangle_face_ids: tuple[int, ...]
    dropped_triangles: int

    @property
    def vertex_count(self) -> int:
        return len(self.positions)

    @property
    def triangle_count(self) -> int:
        return len(self.triangles)


@dataclass(frozen=True, slots=True)
class MeshArrayRecord:
    """Fresh mutable NumPy snapshots at an explicit interop boundary."""

    positions: np.ndarray
    normals: np.ndarray
    triangles: np.ndarray
    triangle_face_ids: np.ndarray


_MESH_SERIALIZER = MeshSerializer()
MESH_SPEC = ResultSpec.for_type(
    ops.MeshValue,
    type_id="zencad.typed.MeshData.v1",
    serializer=_MESH_SERIALIZER,
    validator=ops.valid_mesh,
)


class MeshData(Handle[ops.MeshValue]):
    """Stable indexed mesh containing a resolved snapshot or expression."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ops.MeshValue]] = MESH_SPEC

    @classmethod
    def _from_state(
        cls: type[MeshHandleT],
        context: Context,
        state: State[ops.MeshValue],
    ) -> MeshHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.mesh.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def from_data(
        cls: type[MeshHandleT],
        positions: Sequence[Sequence[float]],
        normals: Sequence[Sequence[float]],
        triangles: Sequence[Sequence[int]],
        triangle_face_ids: Sequence[int],
        *,
        context: Context,
        dropped_triangles: int = 0,
    ) -> MeshHandleT:
        return cls._from_state(
            context,
            ops.mesh_from_data(
                positions,
                normals,
                triangles,
                triangle_face_ids,
                dropped_triangles,
            ),
        )

    def value(self) -> MeshDataRecord:
        value = self._resolved()
        return MeshDataRecord(
            positions=value.positions,
            normals=value.normals,
            triangles=value.triangles,
            triangle_face_ids=value.triangle_face_ids,
            dropped_triangles=value.dropped_triangles,
        )

    @property
    def positions(self) -> tuple[VectorRow, ...]:
        return self._resolved().positions

    @property
    def normals(self) -> tuple[VectorRow, ...]:
        return self._resolved().normals

    @property
    def triangles(self) -> tuple[TriangleRow, ...]:
        return self._resolved().triangles

    @property
    def triangle_face_ids(self) -> tuple[int, ...]:
        return self._resolved().triangle_face_ids

    @property
    def dropped_triangles(self) -> int:
        return self._resolved().dropped_triangles

    @property
    def vertex_count(self) -> int:
        return len(self._resolved().positions)

    @property
    def triangle_count(self) -> int:
        return len(self._resolved().triangles)

    def get_nodes(self) -> tuple[VectorRow, ...]:
        """Compatibility spelling returning immutable numeric node rows."""
        return get_nodes(self)

    def get_triangles(self) -> tuple[TriangleRow, ...]:
        """Compatibility spelling returning immutable zero-based indices."""
        return get_triangles(self)

    def boundbox(self) -> BoundaryBox:
        return mesh_boundbox(self)

    def native(self) -> Poly_Triangulation:
        return mesh_to_poly_triangulation(self)

    def mesh_to_poly_triangulation(self) -> Poly_Triangulation:
        """Legacy spelling for the explicit native triangulation boundary."""
        return mesh_to_poly_triangulation(self)

    def to_numpy(self) -> MeshArrayRecord:
        value = self._resolved()
        return MeshArrayRecord(
            positions=np.array(value.positions, dtype=np.float64),
            normals=np.array(value.normals, dtype=np.float64),
            triangles=np.array(value.triangles, dtype=np.uint32),
            triangle_face_ids=np.array(value.triangle_face_ids, dtype=np.uint32),
        )

    def display_payload(self) -> bytes:
        """Encode the current provenance-free scene mesh transport."""
        return mesh_display_payload(self)

def _positive_number(value: Number, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _crease_angle(value: Number) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("crease_angle must be int or float")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= math.pi:
        raise ValueError("crease_angle must be finite and between zero and pi")
    return result


def _require_shape(value: object, name: str) -> None:
    from .topology import Shape

    if not isinstance(value, Shape):
        raise TypeError(f"{name} expects Shape")


@operation(
    backend=ops.mesh_shape,
    result=MESH_SPEC,
    returns=MeshData,
    operation_id="zencad.typed.shape.to-mesh",
    operation_version="1",
)
def to_mesh(
    shape: Shape,
    linear_deflection: Number = 0.5,
    angular_deflection: Number = 0.6,
    *,
    crease_angle: Number = math.radians(32),
    relative: bool = False,
    parallel: bool = True,
    weld_tolerance: Number | None = None,
) -> OperationArguments:
    """Create a stable indexed mesh while retaining the shape graph."""

    _require_shape(shape, "to_mesh")
    if not isinstance(relative, bool) or not isinstance(parallel, bool):
        raise TypeError("relative and parallel must be bool")
    resolved_weld_tolerance = (
        None
        if weld_tolerance is None
        else _positive_number(weld_tolerance, "weld_tolerance")
    )
    return arguments(
        shape,
        _positive_number(linear_deflection, "linear_deflection"),
        _positive_number(angular_deflection, "angular_deflection"),
        _crease_angle(crease_angle),
        relative,
        parallel,
        resolved_weld_tolerance,
    )


def triangulate(
    face: Face,
    linear_deflection: Number = 0.5,
    angular_deflection: Number = 0.6,
    *,
    crease_angle: Number = math.radians(32),
    relative: bool = False,
    parallel: bool = True,
    weld_tolerance: Number | None = None,
) -> MeshData:
    """Face-specific spelling for :func:`to_mesh`."""

    from .topology import Face

    if not isinstance(face, Face):
        raise TypeError("triangulate expects Face")
    return to_mesh(
        face,
        linear_deflection,
        angular_deflection,
        crease_angle=crease_angle,
        relative=relative,
        parallel=parallel,
        weld_tolerance=weld_tolerance,
    )


@operation(
    backend=ops.mesh_boundary_box,
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.mesh.boundbox",
    operation_version="1",
)
def mesh_boundbox(mesh: MeshData, /) -> OperationArguments:
    if not isinstance(mesh, MeshData):
        raise TypeError("mesh_boundbox expects MeshData")
    return arguments(mesh)


def get_nodes(
    triangulation: MeshData | Poly_Triangulation,
    /,
) -> tuple[VectorRow, ...]:
    """Materialize immutable node rows from typed or native triangulation."""

    if isinstance(triangulation, MeshData):
        return triangulation.positions
    if not isinstance(triangulation, Poly_Triangulation):
        raise TypeError("get_nodes expects MeshData or Poly_Triangulation")
    return tuple(
        (
            float(triangulation.Node(index).X()),
            float(triangulation.Node(index).Y()),
            float(triangulation.Node(index).Z()),
        )
        for index in range(1, triangulation.NbNodes() + 1)
    )


def get_triangles(
    triangulation: MeshData | Poly_Triangulation,
    /,
) -> tuple[TriangleRow, ...]:
    """Materialize immutable zero-based triangle rows."""

    if isinstance(triangulation, MeshData):
        return triangulation.triangles
    if not isinstance(triangulation, Poly_Triangulation):
        raise TypeError("get_triangles expects MeshData or Poly_Triangulation")
    return tuple(
        tuple(value - 1 for value in triangulation.Triangle(index).Get())
        for index in range(1, triangulation.NbTriangles() + 1)
    )


def mesh_to_poly_triangulation(mesh: MeshData, /) -> Poly_Triangulation:
    """Materialize a fresh native triangulation snapshot."""

    if not isinstance(mesh, MeshData):
        raise TypeError("mesh_to_poly_triangulation expects MeshData")
    return ops.mesh_to_poly_triangulation(mesh._resolved())


def mesh_display_payload(mesh: MeshData, /) -> bytes:
    """Materialize the provenance-free scene mesh transport."""

    if not isinstance(mesh, MeshData):
        raise TypeError("mesh_display_payload expects MeshData")
    return ops.mesh_display_payload(mesh._resolved())


__all__ = [
    "MESH_SPEC",
    "MeshArrayRecord",
    "MeshData",
    "MeshDataRecord",
    "get_nodes",
    "get_triangles",
    "mesh_boundbox",
    "mesh_display_payload",
    "mesh_to_poly_triangulation",
    "to_mesh",
    "triangulate",
]
