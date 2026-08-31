"""Typed immutable indexed-mesh handle and explicit materialization records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeVar

import numpy as np
from OCP.Poly import Poly_Triangulation
from evalcache import Expression, ResultSpec

from . import _mesh_operations as ops
from ._core import Handle, State
from ._serialization import MeshSerializer
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox

if TYPE_CHECKING:
    from .runtime import Runtime


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
        runtime: Runtime,
        state: State[ops.MeshValue],
    ) -> MeshHandleT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.mesh.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def from_data(
        cls: type[MeshHandleT],
        positions: Sequence[Sequence[float]],
        normals: Sequence[Sequence[float]],
        triangles: Sequence[Sequence[int]],
        triangle_face_ids: Sequence[int],
        *,
        runtime: Runtime,
        dropped_triangles: int = 0,
    ) -> MeshHandleT:
        return cls._from_state(
            runtime,
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
        return self.positions

    def get_triangles(self) -> tuple[TriangleRow, ...]:
        """Compatibility spelling returning immutable zero-based indices."""
        return self.triangles

    def boundbox(self) -> BoundaryBox:
        state = self.runtime._value_state(
            ops.mesh_boundary_box,
            result=BOUNDARY_BOX_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.mesh.boundbox",
        )
        return BoundaryBox._from_state(self.runtime, state)

    def native(self) -> Poly_Triangulation:
        return ops.mesh_to_poly_triangulation(self._resolved())

    def mesh_to_poly_triangulation(self) -> Poly_Triangulation:
        """Legacy spelling for the explicit native triangulation boundary."""
        return self.native()

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
        return ops.mesh_display_payload(self._resolved())

    def unlazy(self) -> MeshData:
        super().unlazy()
        return self
