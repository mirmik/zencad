"""Typed topology handles containing ZenCad's evaluation graph."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
import math
from typing import (
    TYPE_CHECKING,
    Callable,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
    cast,
    overload,
)

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
from OCP.Geom import Geom_Curve, Geom_Surface
from evalcache import Expression, ResultSpec

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
from .curves import CURVE_SPEC, Curve, CurveKind
from .meshes import MESH_SPEC, MeshData
from .records import (
    CircleParameters,
    EllipseParameters,
    Interval,
    LineParameters,
    ShapeProperties,
)
from .surfaces import SURFACE_SPEC, Surface
from .transforms import AffineTransform, Transform
from .values import (
    POINT3_SPEC,
    SCALAR_SPEC,
    Number,
    Point3,
    Scalar,
    ScalarInput,
    Vector3,
    _scalar_state,
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
BOOL_SPEC = ResultSpec.for_type(bool, type_id="zencad.typed.bool.v1")
SHAPE_KIND_SPEC = ResultSpec.for_type(
    str,
    type_id="zencad.typed.ShapeKind.v1",
    validator=lambda value: (
        value
        in {
            "vertex",
            "edge",
            "wire",
            "face",
            "shell",
            "solid",
            "compsolid",
            "compound",
        }
    ),
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

ShapeKind = Literal[
    "vertex",
    "edge",
    "wire",
    "face",
    "shell",
    "solid",
    "compsolid",
    "compound",
]


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

    def __add__(self, other: Shape) -> Shape:
        from .booleans import _shape_union

        return _shape_union(self, other)

    def __sub__(self, other: Shape) -> Shape:
        from .booleans import _shape_difference

        return _shape_difference(self, other)

    def __xor__(self, other: Shape) -> Shape:
        from .booleans import _shape_intersection

        return _shape_intersection(self, other)

    def unlazy(self: ShapeT) -> ShapeT:
        """Compatibility boundary that materializes and preserves the handle."""
        self._resolved()
        return self

    def transform(
        self: ShapeT,
        transformation: Transform | AffineTransform,
        /,
    ) -> ShapeT:
        """Apply a typed similarity or general affine transformation."""
        if not isinstance(transformation, (Transform, AffineTransform)):
            raise TypeError("Shape.transform expects Transform or AffineTransform")
        require_same_runtime(self.runtime, transformation)
        operation = (
            ops.affine_transform
            if isinstance(transformation, AffineTransform)
            else ops.transform
        )
        expression = self.runtime._expression(
            operation,
            result=self._result_spec,
            args=(self._state, transformation._state),
            operation_id=(
                "zencad.typed.shape.affine_transform"
                if isinstance(transformation, AffineTransform)
                else "zencad.typed.shape.transform"
            ),
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
        vector = self.runtime.vector3(*args)
        expression = self.runtime._expression(
            ops.translate,
            result=self._result_spec,
            args=(self._state, vector._state),
            operation_id="zencad.typed.shape.translate",
        )
        return type(self)._from_state(self.runtime, expression)

    def move(self: ShapeT, *args: object) -> ShapeT:
        return self.transform(self.runtime.move(*args))

    def mov(self: ShapeT, *args: object) -> ShapeT:
        return self.move(*args)

    def moveX(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.moveX(value))

    def moveY(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.moveY(value))

    def moveZ(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.moveZ(value))

    def movX(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveX(value)

    def movY(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveY(value)

    def movZ(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveZ(value)

    def translateX(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveX(value)

    def translateY(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveY(value)

    def translateZ(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.moveZ(value)

    def right(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.right(value))

    def left(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.left(value))

    def forw(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.forw(value))

    def back(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.back(value))

    def up(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.up(value))

    def down(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.down(value))

    def rotate(
        self: ShapeT,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> ShapeT:
        return self.transform(self.runtime.rotate(axis, angle))

    def rot(
        self: ShapeT,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> ShapeT:
        return self.rotate(axis, angle)

    def rotateX(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.rotateX(angle))

    def rotateY(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.rotateY(angle))

    def rotateZ(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.transform(self.runtime.rotateZ(angle))

    def rotX(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.rotateX(angle)

    def rotY(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.rotateY(angle)

    def rotZ(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        return self.rotateZ(angle)

    def scale(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        resolved_center = None if center is None else self.runtime.point3(center)
        return self.transform(self.runtime.scale(factor, center=resolved_center))

    def scaleXYZ(
        self: ShapeT,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        resolved_center = None if center is None else self.runtime.point3(center)
        return self.transform(
            self.runtime.scaleXYZ(x, y, z, center=resolved_center)
        )

    def scaleX(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        resolved_center = None if center is None else self.runtime.point3(center)
        return self.transform(self.runtime.scaleX(factor, center=resolved_center))

    def scaleY(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        resolved_center = None if center is None else self.runtime.point3(center)
        return self.transform(self.runtime.scaleY(factor, center=resolved_center))

    def scaleZ(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        resolved_center = None if center is None else self.runtime.point3(center)
        return self.transform(self.runtime.scaleZ(factor, center=resolved_center))

    def mirror(
        self: ShapeT,
        normal: Vector3 | Sequence[ScalarInput],
        /,
    ) -> ShapeT:
        return self.transform(self.runtime.mirror(self.runtime.vector3(normal)))

    def mirrorX(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorX())

    def mirrorY(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorY())

    def mirrorZ(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorZ())

    def mirrorXY(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorXY())

    def mirrorXZ(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorXZ())

    def mirrorYZ(self: ShapeT) -> ShapeT:
        return self.transform(self.runtime.mirrorYZ())

    def _materialized_bool(
        self,
        operation: Callable[..., bool],
        *args: object,
        operation_id: str,
    ) -> bool:
        state = self.runtime._value_state(
            operation,
            result=BOOL_SPEC,
            args=(self._state, *args),
            operation_id=operation_id,
        )
        if isinstance(state, Expression):
            return self.runtime._resolve(state)
        return state

    def shapetype(self) -> ShapeKind:
        state = self.runtime._value_state(
            ops.shape_kind,
            result=SHAPE_KIND_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.kind",
        )
        if isinstance(state, Expression):
            state = self.runtime._resolve(state)
        return cast(ShapeKind, state)

    def _is_kind(self, kind: TopAbs_ShapeEnum, name: str) -> bool:
        return self._materialized_bool(
            ops.shape_has_kind,
            int(kind),
            operation_id=f"zencad.typed.shape.is_{name}",
        )

    def is_vertex(self) -> bool:
        return self._is_kind(TopAbs_VERTEX, "vertex")

    def is_edge(self) -> bool:
        return self._is_kind(TopAbs_EDGE, "edge")

    def is_wire(self) -> bool:
        return self._is_kind(TopAbs_WIRE, "wire")

    def is_face(self) -> bool:
        return self._is_kind(TopAbs_FACE, "face")

    def is_shell(self) -> bool:
        return self._is_kind(TopAbs_SHELL, "shell")

    def is_solid(self) -> bool:
        return self._is_kind(TopAbs_SOLID, "solid")

    def is_compsolid(self) -> bool:
        return self._is_kind(TopAbs_COMPSOLID, "compsolid")

    def is_compound(self) -> bool:
        return self._is_kind(TopAbs_COMPOUND, "compound")

    def is_wire_or_edge(self) -> bool:
        return self._materialized_bool(
            ops.shape_is_wire_or_edge,
            operation_id="zencad.typed.shape.is_wire_or_edge",
        )

    def is_closed(self) -> bool:
        return self._materialized_bool(
            ops.shape_is_closed,
            operation_id="zencad.typed.shape.is_closed",
        )

    def is_volumed(self) -> bool:
        return self._materialized_bool(
            ops.shape_is_volumed,
            operation_id="zencad.typed.shape.is_volumed",
        )

    def Wire_orEdgeToWire(self) -> Wire:
        expression = self.runtime._expression(
            ops.wire_from_wire_or_edge,
            result=WIRE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.to_wire",
        )
        return Wire._from_state(self.runtime, expression)

    def to_wire(self) -> Wire:
        return self.Wire_orEdgeToWire()

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

    def native_vertices(self) -> DeferredSequence[Vertex]:
        return self.vertices()

    def curve(self) -> Curve:
        state = self.runtime._value_state(
            ops.edge_curve,
            result=CURVE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.curve",
        )
        return Curve._from_state(self.runtime, state)

    def Curve(self) -> Geom_Curve:
        return self.curve().native()

    def AdaptorCurve(self) -> Geom_Curve:
        return self.curve().native()

    def HCurveAdaptor(self) -> Geom_Curve:
        return self.curve().native()

    def d0(self, parameter: ScalarInput, /) -> Point3:
        return self.curve().point(parameter)

    def value(self, parameter: ScalarInput, /) -> Point3:
        return self.d0(parameter)

    def d1(self, parameter: ScalarInput, /) -> Vector3:
        return self.curve().tangent(parameter)

    def range(self) -> Interval:
        return self.curve().range()

    def endpoints(self) -> tuple[Point3, Point3]:
        start = self.runtime._value_state(
            ops.shape_endpoint,
            result=POINT3_SPEC,
            args=(self._state, False),
            operation_id="zencad.typed.shape.endpoint.start",
        )
        end = self.runtime._value_state(
            ops.shape_endpoint,
            result=POINT3_SPEC,
            args=(self._state, True),
            operation_id="zencad.typed.shape.endpoint.end",
        )
        return (
            Point3._from_state(self.runtime, start),
            Point3._from_state(self.runtime, end),
        )

    def curvetype(self) -> CurveKind:
        return self.curve().curvetype()

    def line_parameters(self) -> LineParameters:
        return self.curve().line_parameters()

    def circle_parameters(self) -> CircleParameters:
        return self.curve().circle_parameters()

    def ellipse_parameters(self) -> EllipseParameters:
        return self.curve().ellipse_parameters()

    def lower_distance_parameter(self, pnt: Point3) -> Scalar:
        return self.curve().lower_distance_parameter(pnt)

    def trimmed_edge(self, start: ScalarInput, finish: ScalarInput) -> Edge:
        return self.curve().trimmed_edge(start, finish)

    def uniform(
        self,
        npoints: int,
        strt: ScalarInput | None = None,
        fini: ScalarInput | None = None,
    ) -> list[Scalar]:
        return self.curve().uniform(npoints, strt, fini)

    def uniform_points(
        self,
        npoints: int,
        strt: ScalarInput | None = None,
        fini: ScalarInput | None = None,
    ) -> list[Point3]:
        return self.curve().uniform_points(npoints, strt, fini)

    def surface(self) -> Surface:
        state = self.runtime._value_state(
            ops.face_surface,
            result=SURFACE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface",
        )
        return Surface._from_state(self.runtime, state)

    def AdaptorSurface(self) -> Geom_Surface:
        return self.surface().native()

    def normal(
        self,
        u: ScalarInput = 0,
        v: ScalarInput = 0,
    ) -> Vector3:
        return self.surface().normal(u, v)

    def SurfaceProperties(self) -> ShapeProperties:
        center = self.runtime._value_state(
            ops.surface_center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface_properties.center",
        )
        mass = self.runtime._value_state(
            ops.surface_mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface_properties.mass",
        )
        return ShapeProperties(
            Point3._from_state(self.runtime, center),
            Scalar._from_state(self.runtime, mass),
        )

    def VolumeProperties(self) -> ShapeProperties:
        center = self.runtime._value_state(
            ops.volume_center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.volume_properties.center",
        )
        mass = self.runtime._value_state(
            ops.volume_mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.volume_properties.mass",
        )
        return ShapeProperties(
            Point3._from_state(self.runtime, center),
            Scalar._from_state(self.runtime, mass),
        )

    def fill(self) -> Face:
        expression = self.runtime._expression(
            ops.fill_shape,
            result=FACE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.fill",
        )
        return Face._from_state(self.runtime, expression)

    def extrude(
        self,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        if not isinstance(center, bool):
            raise TypeError("extrude center must be bool")
        resolved_vector = (
            self.runtime.vector3(0, 0, vec)
            if isinstance(vec, (Scalar, int, float)) and not isinstance(vec, bool)
            else self.runtime.vector3(vec)
        )
        expression = self.runtime._expression(
            ops.extrude_shape,
            result=SHAPE_SPEC,
            args=(self._state, resolved_vector._state, center),
            operation_id="zencad.typed.shape.extrude",
        )
        return Shape._from_state(self.runtime, expression)

    def linear_extrude(
        self,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        """Compatibility spelling for :meth:`extrude`."""
        return self.extrude(vec, center)

    def revol(
        self,
        r: ScalarInput | None = None,
        yaw: ScalarInput = 0,
    ) -> Shape:
        expression = self.runtime._expression(
            ops.revolve_shape,
            result=SHAPE_SPEC,
            args=(
                self._state,
                None if r is None else _scalar_state(self.runtime, r),
                _scalar_state(self.runtime, yaw),
            ),
            operation_id="zencad.typed.shape.revol",
        )
        return Shape._from_state(self.runtime, expression)

    def _reference_states(
        self,
        references: Sequence[Point3] | None,
        name: str,
    ) -> tuple[State[ops.Point3Value], ...] | None:
        if references is None:
            return None
        values = tuple(references)
        for value in values:
            if not isinstance(value, Point3):
                raise TypeError(f"{name} references must be Point3 values")
            require_same_runtime(self.runtime, value)
        return tuple(value._state for value in values)

    def _rounded_operation(
        self,
        operation: Callable[..., ResolvedShape],
        radius: ScalarInput,
        references: Sequence[Point3] | None,
        name: str,
        result_spec: ResultSpec[ResolvedShape] = SHAPE_SPEC,
    ) -> Shape:
        expression = self.runtime._expression(
            operation,
            result=result_spec,
            args=(
                self._state,
                _scalar_state(self.runtime, radius),
                self._reference_states(references, name),
            ),
            operation_id=f"zencad.typed.shape.{name}",
        )
        return Shape._from_state(self.runtime, expression)

    def fillet(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Shape:
        return self._rounded_operation(ops.fillet_shape, r, refs, "fillet")

    def chamfer(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Shape:
        return self._rounded_operation(ops.chamfer_shape, r, refs, "chamfer")

    def fillet2d(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Face:
        expression = self.runtime._expression(
            ops.fillet2d_shape,
            result=FACE_SPEC,
            args=(
                self._state,
                _scalar_state(self.runtime, r),
                self._reference_states(refs, "fillet2d"),
            ),
            operation_id="zencad.typed.shape.fillet2d",
        )
        return Face._from_state(self.runtime, expression)

    def chamfer2d(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Face:
        expression = self.runtime._expression(
            ops.chamfer2d_shape,
            result=FACE_SPEC,
            args=(
                self._state,
                _scalar_state(self.runtime, r),
                self._reference_states(refs, "chamfer2d"),
            ),
            operation_id="zencad.typed.shape.chamfer2d",
        )
        return Face._from_state(self.runtime, expression)

    def restore_shapetype(self) -> Shape:
        """Recover a precise topology handle when exactly one subtype exists."""
        return self.runtime.restore_shapetype(self)

    def offset(self, distance: ScalarInput, /) -> Shape:
        expression = self.runtime._expression(
            ops.offset_shape,
            result=SHAPE_SPEC,
            args=(self._state, _scalar_state(self.runtime, distance)),
            operation_id="zencad.typed.shape.offset",
        )
        return Shape._from_state(self.runtime, expression)

    def unify(self: ShapeT) -> ShapeT:
        expression = self.runtime._expression(
            ops.unify_shape,
            result=self._result_spec,
            args=(self._state,),
            operation_id="zencad.typed.shape.unify",
        )
        return type(self)._from_state(self.runtime, expression)

    def _near(
        self,
        point: Point3,
        operation: Callable[[ResolvedShape, ops.Point3Value], ResolvedShape],
        result_spec: ResultSpec[ResolvedShape],
        handle_type: type[ShapeHandleT],
        name: str,
    ) -> ShapeHandleT:
        if not isinstance(point, Point3):
            raise TypeError(f"near_{name} expects Point3")
        require_same_runtime(self.runtime, point)
        expression = self.runtime._expression(
            operation,
            result=result_spec,
            args=(self._state, point._state),
            operation_id=f"zencad.typed.shape.near_{name}",
        )
        return handle_type._from_state(self.runtime, expression)

    def near_vertex(self, point: Point3, /) -> Vertex:
        return self._near(point, ops.near_vertex, VERTEX_SPEC, Vertex, "vertex")

    def near_edge(self, point: Point3, /) -> Edge:
        return self._near(point, ops.near_edge, EDGE_SPEC, Edge, "edge")

    def near_wire(self, point: Point3, /) -> Wire:
        return self._near(point, ops.near_wire, WIRE_SPEC, Wire, "wire")

    def near_face(self, point: Point3, /) -> Face:
        return self._near(point, ops.near_face, FACE_SPEC, Face, "face")

    def near_shell(self, point: Point3, /) -> Shell:
        return self._near(point, ops.near_shell, SHELL_SPEC, Shell, "shell")

    def near_solid(self, point: Point3, /) -> Solid:
        return self._near(point, ops.near_solid, SOLID_SPEC, Solid, "solid")

    def near_compsolid(self, point: Point3, /) -> CompSolid:
        return self._near(
            point,
            ops.near_compsolid,
            COMPSOLID_SPEC,
            CompSolid,
            "compsolid",
        )

    def near_compound(self, point: Point3, /) -> Compound:
        return self._near(
            point,
            ops.near_compound,
            COMPOUND_SPEC,
            Compound,
            "compound",
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

    def curve(self) -> Curve:
        state = self.runtime._value_state(
            ops.edge_curve,
            result=CURVE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.edge.curve",
        )
        return Curve._from_state(self.runtime, state)

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

    def surface(self) -> Surface:
        state = self.runtime._value_state(
            ops.face_surface,
            result=SURFACE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.face.surface",
        )
        return Surface._from_state(self.runtime, state)

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

    def thicksolid(
        self,
        thickness: ScalarInput,
        references: Sequence[Point3],
        /,
    ) -> Solid:
        reference_states = self._reference_states(references, "thicksolid")
        assert reference_states is not None
        expression = self.runtime._expression(
            ops.thicksolid_shape,
            result=SOLID_SPEC,
            args=(
                self._state,
                _scalar_state(self.runtime, thickness),
                reference_states,
            ),
            operation_id="zencad.typed.solid.thicksolid",
        )
        return Solid._from_state(self.runtime, expression)

    def shapefix_solid(self) -> Solid:
        expression = self.runtime._expression(
            ops.shapefix_solid_shape,
            result=SOLID_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.solid.shapefix",
        )
        return Solid._from_state(self.runtime, expression)

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
