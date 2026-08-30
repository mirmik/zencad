"""Typed topology handles containing ZenCad's evaluation graph."""

from __future__ import annotations

from collections.abc import Iterator
import math
from typing import TYPE_CHECKING, Callable, ClassVar, Generic, TypeVar, cast, overload

from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHELL,
    TopAbs_SOLID,
    TopAbs_VERTEX,
    TopAbs_WIRE,
    TopAbs_ShapeEnum,
)
from OCP.TopoDS import (
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
)
from evalcache.v2 import Expression, ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.occ_compat import (
    as_compound,
    as_compsolid,
    as_edge,
    as_face,
    as_shell,
    as_solid,
    as_vertex,
    as_wire,
)
from zencad.runtime.scene_protocol import encode_brep

from . import _operations as ops
from . import _bound_operations as bound_ops
from . import _mesh_operations as mesh_ops
from ._core import Handle, State, require_same_runtime
from ._serialization import ShapeBrepSerializer
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .meshes import MESH_SPEC, MeshData
from .transforms import Transform
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    Number,
    Point3,
    Scalar,
    ScalarInput,
    Vector3,
)

if TYPE_CHECKING:
    from .runtime import Runtime


ShapeT = TypeVar("ShapeT", bound="Shape")
ShapeHandleT = TypeVar("ShapeHandleT", bound="Shape")


_SHAPE_SERIALIZER = ShapeBrepSerializer()


def _valid_shape(value: ResolvedShape) -> bool:
    native = value.Shape()
    return not native.IsNull()


def _topology_validator(
    kind: TopAbs_ShapeEnum,
) -> Callable[[ResolvedShape], bool]:
    def validate(value: ResolvedShape) -> bool:
        native = value.Shape()
        return not native.IsNull() and native.ShapeType() == kind

    return validate


def _topology_spec(name: str, kind: TopAbs_ShapeEnum) -> ResultSpec[ResolvedShape]:
    return ResultSpec.for_type(
        ResolvedShape,
        type_id=f"zencad.typed.{name}.v1",
        serializer=_SHAPE_SERIALIZER,
        validator=_topology_validator(kind),
    )


def _topology_sequence_spec(
    name: str,
    kind: TopAbs_ShapeEnum,
) -> ResultSpec[tuple[ResolvedShape, ...]]:
    item_validator = _topology_validator(kind)
    return cast(
        ResultSpec[tuple[ResolvedShape, ...]],
        ResultSpec.for_type(
            tuple,
            type_id=f"zencad.typed.Sequence[{name}].v1",
            validator=lambda values: all(
                isinstance(value, ResolvedShape) and item_validator(value)
                for value in values
            ),
        ),
    )


SHAPE_SPEC = ResultSpec.for_type(
    ResolvedShape,
    type_id="zencad.typed.Shape.v1",
    serializer=_SHAPE_SERIALIZER,
    validator=_valid_shape,
)
VERTEX_SPEC = _topology_spec("Vertex", TopAbs_VERTEX)
EDGE_SPEC = _topology_spec("Edge", TopAbs_EDGE)
WIRE_SPEC = _topology_spec("Wire", TopAbs_WIRE)
FACE_SPEC = _topology_spec("Face", TopAbs_FACE)
SHELL_SPEC = _topology_spec("Shell", TopAbs_SHELL)
SOLID_SPEC = _topology_spec("Solid", TopAbs_SOLID)
COMPOUND_SPEC = _topology_spec("Compound", TopAbs_COMPOUND)
COMPSOLID_SPEC = _topology_spec("CompSolid", TopAbs_COMPSOLID)

_VERTEX_SEQUENCE_SPEC = _topology_sequence_spec("Vertex", TopAbs_VERTEX)
_EDGE_SEQUENCE_SPEC = _topology_sequence_spec("Edge", TopAbs_EDGE)
_WIRE_SEQUENCE_SPEC = _topology_sequence_spec("Wire", TopAbs_WIRE)
_FACE_SEQUENCE_SPEC = _topology_sequence_spec("Face", TopAbs_FACE)
_SHELL_SEQUENCE_SPEC = _topology_sequence_spec("Shell", TopAbs_SHELL)
_SOLID_SEQUENCE_SPEC = _topology_sequence_spec("Solid", TopAbs_SOLID)
_COMPOUND_SEQUENCE_SPEC = _topology_sequence_spec("Compound", TopAbs_COMPOUND)
_COMPSOLID_SEQUENCE_SPEC = _topology_sequence_spec("CompSolid", TopAbs_COMPSOLID)


def _mesh_positive_number(value: Number, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _mesh_crease_angle(value: Number) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("crease_angle must be int or float")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= math.pi:
        raise ValueError("crease_angle must be finite and between zero and pi")
    return result


class Shape(Handle[ResolvedShape]):
    """A non-null topological shape with a hidden resolved value or graph."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ResolvedShape]] = SHAPE_SPEC

    @classmethod
    def _from_state(
        cls: type[ShapeT],
        runtime: Runtime,
        state: State[ResolvedShape],
    ) -> ShapeT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.shape.bind")
        value = cls.__new__(cls)
        value._bind(runtime, state)
        return value

    @classmethod
    def _from_expression(
        cls: type[ShapeT],
        runtime: Runtime,
        expression: Expression[ResolvedShape],
    ) -> ShapeT:
        """Compatibility spelling for callers predating generic state binding."""
        return cls._from_state(runtime, expression)

    @classmethod
    def from_ocp(
        cls: type[ShapeT],
        value: TopoDS_Shape,
        *,
        runtime: Runtime,
    ) -> ShapeT:
        """Snapshot a native OCP shape into an immutable typed handle."""
        if not isinstance(value, TopoDS_Shape):
            raise TypeError(f"{cls.__name__}.from_ocp expects TopoDS_Shape")
        if value.IsNull():
            raise ValueError("typed topology handles cannot contain a null shape")
        operation_id = f"zencad.typed.{cls.__name__.lower()}.from_ocp"
        cls._result_spec.validate(
            ResolvedShape(value),
            operation_id,
        )
        expression = runtime._expression(
            ops.shape_from_brep,
            result=cls._result_spec,
            args=(encode_brep(value),),
            operation_id=operation_id,
            cacheable=False,
        )
        return cls._from_state(
            runtime,
            expression,
        )

    def _boolean(
        self,
        other: Shape,
        operation: Callable[[ResolvedShape, ResolvedShape], ResolvedShape],
        operation_id: str,
        name: str,
    ) -> Shape:
        if not isinstance(other, Shape):
            raise TypeError(f"Shape {name} expects Shape")
        require_same_runtime(self.runtime, other)
        expression = self.runtime._expression(
            operation,
            result=SHAPE_SPEC,
            args=(self._state, other._state),
            operation_id=operation_id,
        )
        return Shape._from_state(self.runtime, expression)

    def __add__(self, other: Shape) -> Shape:
        return self._boolean(
            other,
            ops.union,
            "zencad.typed.shape.union",
            "union",
        )

    def __sub__(self, other: Shape) -> Shape:
        return self._boolean(
            other,
            ops.difference,
            "zencad.typed.shape.difference",
            "difference",
        )

    def __xor__(self, other: Shape) -> Shape:
        return self._boolean(
            other,
            ops.intersection,
            "zencad.typed.shape.intersection",
            "intersection",
        )

    def unlazy(self: ShapeT) -> ShapeT:
        """Compatibility boundary that materializes and preserves the handle."""
        self._resolved()
        return self

    def transform(self: ShapeT, transformation: Transform, /) -> ShapeT:
        """Apply a typed similarity transform without changing topology kind."""
        if not isinstance(transformation, Transform):
            raise TypeError("Shape.transform expects Transform")
        require_same_runtime(self.runtime, transformation)
        expression = self.runtime._expression(
            ops.transform,
            result=self._result_spec,
            args=(self._state, transformation._state),
            operation_id="zencad.typed.shape.transform",
        )
        return type(self)._from_state(self.runtime, expression)

    @overload
    def translate(self: ShapeT, vector: Vector3, /) -> ShapeT: ...

    @overload
    def translate(
        self: ShapeT,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
    ) -> ShapeT: ...

    def translate(self: ShapeT, *args: object) -> ShapeT:
        if len(args) == 1 and isinstance(args[0], Vector3):
            vector = args[0]
            require_same_runtime(self.runtime, vector)
        elif len(args) == 3:
            vector = Vector3(
                cast(ScalarInput, args[0]),
                cast(ScalarInput, args[1]),
                cast(ScalarInput, args[2]),
                runtime=self.runtime,
            )
        else:
            raise TypeError("translate expects Vector3 or three scalar coordinates")
        expression = self.runtime._expression(
            ops.translate,
            result=self._result_spec,
            args=(self._state, vector._state),
            operation_id="zencad.typed.shape.translate",
        )
        return type(self)._from_state(self.runtime, expression)

    def _topology_query(
        self,
        operation: Callable[[ResolvedShape], tuple[ResolvedShape, ...]],
        *,
        sequence_spec: ResultSpec[tuple[ResolvedShape, ...]],
        item_type: type[ShapeHandleT],
        item_spec: ResultSpec[ResolvedShape],
        operation_id: str,
    ) -> DeferredSequence[ShapeHandleT]:
        expression = self.runtime._expression(
            operation,
            result=sequence_spec,
            args=(self._state,),
            operation_id=operation_id,
            cacheable=False,
        )
        return DeferredSequence(
            self.runtime,
            expression,
            item_type=item_type,
            item_spec=item_spec,
            operation_id=f"{operation_id}.item",
        )

    def vertices(self) -> DeferredSequence[Vertex]:
        return self._topology_query(
            ops.vertices,
            sequence_spec=_VERTEX_SEQUENCE_SPEC,
            item_type=Vertex,
            item_spec=VERTEX_SPEC,
            operation_id="zencad.typed.shape.vertices",
        )

    def edges(self) -> DeferredSequence[Edge]:
        return self._topology_query(
            ops.edges,
            sequence_spec=_EDGE_SEQUENCE_SPEC,
            item_type=Edge,
            item_spec=EDGE_SPEC,
            operation_id="zencad.typed.shape.edges",
        )

    def wires(self) -> DeferredSequence[Wire]:
        return self._topology_query(
            ops.wires,
            sequence_spec=_WIRE_SEQUENCE_SPEC,
            item_type=Wire,
            item_spec=WIRE_SPEC,
            operation_id="zencad.typed.shape.wires",
        )

    def faces(self) -> DeferredSequence[Face]:
        return self._topology_query(
            ops.faces,
            sequence_spec=_FACE_SEQUENCE_SPEC,
            item_type=Face,
            item_spec=FACE_SPEC,
            operation_id="zencad.typed.shape.faces",
        )

    def shells(self) -> DeferredSequence[Shell]:
        return self._topology_query(
            ops.shells,
            sequence_spec=_SHELL_SEQUENCE_SPEC,
            item_type=Shell,
            item_spec=SHELL_SPEC,
            operation_id="zencad.typed.shape.shells",
        )

    def solids(self) -> DeferredSequence[Solid]:
        return self._topology_query(
            ops.solids,
            sequence_spec=_SOLID_SEQUENCE_SPEC,
            item_type=Solid,
            item_spec=SOLID_SPEC,
            operation_id="zencad.typed.shape.solids",
        )

    def compounds(self) -> DeferredSequence[Compound]:
        return self._topology_query(
            ops.compounds,
            sequence_spec=_COMPOUND_SEQUENCE_SPEC,
            item_type=Compound,
            item_spec=COMPOUND_SPEC,
            operation_id="zencad.typed.shape.compounds",
        )

    def compsolids(self) -> DeferredSequence[CompSolid]:
        return self._topology_query(
            ops.compsolids,
            sequence_spec=_COMPSOLID_SEQUENCE_SPEC,
            item_type=CompSolid,
            item_spec=COMPSOLID_SPEC,
            operation_id="zencad.typed.shape.compsolids",
        )

    def mass(self) -> Scalar:
        state = self.runtime._value_state(
            ops.mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.mass",
        )
        return Scalar._from_state(self.runtime, state)

    def center(self) -> Point3:
        state = self.runtime._value_state(
            ops.center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.center",
        )
        return Point3._from_state(self.runtime, state)

    def boundbox(self) -> BoundaryBox:
        """Return graph-preserving axis-aligned bounds for this shape."""
        expression = self.runtime._expression(
            bound_ops.shape_boundary_box,
            result=BOUNDARY_BOX_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.boundbox",
        )
        return BoundaryBox._from_state(self.runtime, expression)

    def bbox(self) -> BoundaryBox:
        """Short alias for :meth:`boundbox`."""
        return self.boundbox()

    def to_mesh(
        self,
        linear_deflection: Number = 0.5,
        angular_deflection: Number = 0.6,
        *,
        crease_angle: Number = math.radians(32),
        relative: bool = False,
        parallel: bool = True,
        weld_tolerance: Number | None = None,
    ) -> MeshData:
        """Create a stable indexed mesh while retaining this shape graph."""
        if not isinstance(relative, bool) or not isinstance(parallel, bool):
            raise TypeError("relative and parallel must be bool")
        resolved_weld_tolerance = (
            None
            if weld_tolerance is None
            else _mesh_positive_number(weld_tolerance, "weld_tolerance")
        )
        expression = self.runtime._expression(
            mesh_ops.mesh_shape,
            result=MESH_SPEC,
            args=(
                self._state,
                _mesh_positive_number(linear_deflection, "linear_deflection"),
                _mesh_positive_number(angular_deflection, "angular_deflection"),
                _mesh_crease_angle(crease_angle),
                relative,
                parallel,
                resolved_weld_tolerance,
            ),
            operation_id="zencad.typed.shape.to-mesh",
        )
        return MeshData._from_state(self.runtime, expression)

    def native(self) -> TopoDS_Shape:
        """Materialize an independent snapshot at the explicit OCP boundary."""
        return ops.shape_to_ocp(self._resolved())

    def _legacy(self) -> ResolvedShape:
        """Temporary borrowed adapter for existing internal display/export code."""
        return self._resolved()


class Vertex(Shape):
    __slots__ = ()
    _result_spec = VERTEX_SPEC

    def point(self) -> Point3:
        """Return this topological vertex's geometric position."""
        state = self.runtime._value_state(
            ops.vertex_point,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vertex.point",
        )
        return Point3._from_state(self.runtime, state)

    def native(self) -> TopoDS_Vertex:
        return as_vertex(super().native())


class Edge(Shape):
    __slots__ = ()
    _result_spec = EDGE_SPEC

    def native(self) -> TopoDS_Edge:
        return as_edge(super().native())


class Wire(Shape):
    __slots__ = ()
    _result_spec = WIRE_SPEC

    def native(self) -> TopoDS_Wire:
        return as_wire(super().native())


class Face(Shape):
    __slots__ = ()
    _result_spec = FACE_SPEC

    def triangulate(
        self,
        linear_deflection: Number = 0.5,
        angular_deflection: Number = 0.6,
        *,
        crease_angle: Number = math.radians(32),
        relative: bool = False,
        parallel: bool = True,
        weld_tolerance: Number | None = None,
    ) -> MeshData:
        """Truthful typed replacement for legacy ``triangulate_face``."""
        return self.to_mesh(
            linear_deflection,
            angular_deflection,
            crease_angle=crease_angle,
            relative=relative,
            parallel=parallel,
            weld_tolerance=weld_tolerance,
        )

    def native(self) -> TopoDS_Face:
        return as_face(super().native())


class Shell(Shape):
    __slots__ = ()
    _result_spec = SHELL_SPEC

    def native(self) -> TopoDS_Shell:
        return as_shell(super().native())


class Solid(Shape):
    __slots__ = ()
    _result_spec = SOLID_SPEC

    def native(self) -> TopoDS_Solid:
        return as_solid(super().native())


class Compound(Shape):
    __slots__ = ()
    _result_spec = COMPOUND_SPEC

    def native(self) -> TopoDS_Compound:
        return as_compound(super().native())


class CompSolid(Shape):
    __slots__ = ()
    _result_spec = COMPSOLID_SPEC

    def native(self) -> TopoDS_CompSolid:
        return as_compsolid(super().native())


class DeferredSequence(Generic[ShapeHandleT]):
    """Typed topology sequence whose indexing composes an expression node."""

    __slots__ = (
        "_expression",
        "_item_spec",
        "_item_type",
        "_operation_id",
        "_runtime",
    )

    def __init__(
        self,
        runtime: Runtime,
        expression: Expression[tuple[ResolvedShape, ...]],
        *,
        item_type: type[ShapeHandleT],
        item_spec: ResultSpec[ResolvedShape],
        operation_id: str,
    ) -> None:
        self._runtime = runtime
        self._expression = expression
        self._item_type = item_type
        self._item_spec = item_spec
        self._operation_id = operation_id

    def __getitem__(self, index: int) -> ShapeHandleT:
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("typed sequence indices must be integers")
        expression = self._runtime._expression(
            ops.sequence_item,
            result=self._item_spec,
            args=(self._expression, index),
            operation_id=self._operation_id,
        )
        return self._item_type._from_state(self._runtime, expression)

    def __len__(self) -> int:
        return len(self._runtime._resolve(self._expression))

    def __iter__(self) -> Iterator[ShapeHandleT]:
        for index in range(len(self)):
            yield self[index]
