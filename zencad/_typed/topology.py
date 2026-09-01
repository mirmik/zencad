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
from zencad.geom.validation import ValidationReport
from zencad.operation import using_context
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
from . import _selector_operations as selector_ops
from . import transforms as transform_api
from ._core import Handle, State
from ._serialization import ShapeBrepSerializer
from .bounds import BoundaryBox
from .curves import CURVE_SPEC, Curve, CurveKind
from .meshes import MeshData
from .records import (
    CircleParameters,
    EllipseParameters,
    Interval,
    LineParameters,
    ShapeProperties,
)
from .selectors import Axis, GeomType, Plane
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
    point3,
    vector3,
)

if TYPE_CHECKING:
    from .context import Context


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


class Shape(Handle[ResolvedShape]):
    """A non-null topological shape with a hidden resolved value or graph."""

    __slots__ = ()
    _result_spec: ClassVar[ResultSpec[ResolvedShape]] = SHAPE_SPEC

    @classmethod
    def _from_state(
        cls: type[ShapeT],
        context: Context,
        state: State[ResolvedShape],
    ) -> ShapeT:
        if not isinstance(state, Expression):
            state = cls._result_spec.validate(state, "zencad.typed.shape.bind")
        value = cls.__new__(cls)
        value._bind(context, state)
        return value

    @classmethod
    def _from_expression(
        cls: type[ShapeT],
        context: Context,
        expression: Expression[ResolvedShape],
    ) -> ShapeT:
        """Compatibility spelling for callers predating generic state binding."""
        return cls._from_state(context, expression)

    @classmethod
    def from_ocp(
        cls: type[ShapeT],
        value: TopoDS_Shape,
        *,
        context: Context,
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
        expression = context._expression(
            ops.shape_from_brep,
            result=cls._result_spec,
            args=(encode_brep(value),),
            operation_id=operation_id,
            cacheable=False,
        )
        return cls._from_state(
            context,
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

    def transform(
        self: ShapeT,
        transformation: Transform | AffineTransform,
        /,
    ) -> ShapeT:
        """Apply a typed similarity or general affine transformation."""
        if not isinstance(transformation, (Transform, AffineTransform)):
            raise TypeError("Shape.transform expects Transform or AffineTransform")
        from .shape_transforms import _shape_affine_transform, _shape_transform

        if isinstance(transformation, AffineTransform):
            return cast(ShapeT, _shape_affine_transform(self, transformation))
        return cast(ShapeT, _shape_transform(self, transformation))

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
        from .shape_transforms import _shape_translate

        with using_context(self.context):
            vector = vector3(*args)
            return cast(ShapeT, _shape_translate(self, vector))

    def move(self: ShapeT, *args: object) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.move(*args))

    def mov(self: ShapeT, *args: object) -> ShapeT:
        return self.move(*args)

    def moveX(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.moveX(value))

    def moveY(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.moveY(value))

    def moveZ(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.moveZ(value))

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
        with using_context(self.context):
            return self.transform(transform_api.right(value))

    def left(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.left(value))

    def forw(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.forw(value))

    def back(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.back(value))

    def up(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.up(value))

    def down(self: ShapeT, value: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.down(value))

    def rotate(
        self: ShapeT,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.rotate(axis, angle))

    def rot(
        self: ShapeT,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> ShapeT:
        return self.rotate(axis, angle)

    def rotateX(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.rotateX(angle))

    def rotateY(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.rotateY(angle))

    def rotateZ(self: ShapeT, angle: ScalarInput, /) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.rotateZ(angle))

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
        with using_context(self.context):
            resolved_center = None if center is None else point3(center)
            return self.transform(transform_api.scale(factor, center=resolved_center))

    def scaleXYZ(
        self: ShapeT,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        with using_context(self.context):
            resolved_center = None if center is None else point3(center)
            return self.transform(
                transform_api.scaleXYZ(x, y, z, center=resolved_center)
            )

    def scaleX(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        with using_context(self.context):
            resolved_center = None if center is None else point3(center)
            return self.transform(
                transform_api.scaleX(factor, center=resolved_center)
            )

    def scaleY(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        with using_context(self.context):
            resolved_center = None if center is None else point3(center)
            return self.transform(
                transform_api.scaleY(factor, center=resolved_center)
            )

    def scaleZ(
        self: ShapeT,
        factor: ScalarInput,
        center: Point3 | Sequence[ScalarInput] | None = None,
        /,
    ) -> ShapeT:
        with using_context(self.context):
            resolved_center = None if center is None else point3(center)
            return self.transform(
                transform_api.scaleZ(factor, center=resolved_center)
            )

    def mirror(
        self: ShapeT,
        normal: Vector3 | Sequence[ScalarInput],
        /,
    ) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirror(vector3(normal)))

    def mirrorX(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorX())

    def mirrorY(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorY())

    def mirrorZ(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorZ())

    def mirrorXY(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorXY())

    def mirrorXZ(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorXZ())

    def mirrorYZ(self: ShapeT) -> ShapeT:
        with using_context(self.context):
            return self.transform(transform_api.mirrorYZ())

    def _materialized_bool(
        self,
        operation: Callable[..., bool],
        *args: object,
        operation_id: str,
    ) -> bool:
        state = self.context._value_state(
            operation,
            result=BOOL_SPEC,
            args=(self._state, *args),
            operation_id=operation_id,
        )
        if isinstance(state, Expression):
            return self.context._resolve(state)
        return state

    def shapetype(self) -> ShapeKind:
        state = self.context._value_state(
            ops.shape_kind,
            result=SHAPE_KIND_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.kind",
        )
        if isinstance(state, Expression):
            state = self.context._resolve(state)
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
        expression = self.context._expression(
            ops.wire_from_wire_or_edge,
            result=WIRE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.to_wire",
        )
        return Wire._from_state(self.context, expression)

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
    ) -> ShapeList[ShapeHandleT]:
        expression = self.context._expression(
            operation,
            result=sequence_spec,
            args=(self._state,),
            operation_id=operation_id,
            cacheable=False,
        )
        return ShapeList(
            self.context,
            expression,
            sequence_spec=sequence_spec,
            item_type=item_type,
            item_spec=item_spec,
            operation_id=f"{operation_id}.item",
        )

    def vertices(self) -> ShapeList[Vertex]:
        return self._topology_query(
            ops.vertices,
            sequence_spec=_VERTEX_SEQUENCE_SPEC,
            item_type=Vertex,
            item_spec=VERTEX_SPEC,
            operation_id="zencad.typed.shape.vertices",
        )

    def native_vertices(self) -> ShapeList[Vertex]:
        return self.vertices()

    def curve(self) -> Curve:
        state = self.context._value_state(
            ops.edge_curve,
            result=CURVE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.curve",
        )
        return Curve._from_state(self.context, state)

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
        start = self.context._value_state(
            ops.shape_endpoint,
            result=POINT3_SPEC,
            args=(self._state, False),
            operation_id="zencad.typed.shape.endpoint.start",
        )
        end = self.context._value_state(
            ops.shape_endpoint,
            result=POINT3_SPEC,
            args=(self._state, True),
            operation_id="zencad.typed.shape.endpoint.end",
        )
        return (
            Point3._from_state(self.context, start),
            Point3._from_state(self.context, end),
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
        state = self.context._value_state(
            ops.face_surface,
            result=SURFACE_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface",
        )
        return Surface._from_state(self.context, state)

    def AdaptorSurface(self) -> Geom_Surface:
        return self.surface().native()

    def normal(
        self,
        u: ScalarInput = 0,
        v: ScalarInput = 0,
    ) -> Vector3:
        return self.surface().normal(u, v)

    def SurfaceProperties(self) -> ShapeProperties:
        center = self.context._value_state(
            ops.surface_center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface_properties.center",
        )
        mass = self.context._value_state(
            ops.surface_mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.surface_properties.mass",
        )
        return ShapeProperties(
            Point3._from_state(self.context, center),
            Scalar._from_state(self.context, mass),
        )

    def VolumeProperties(self) -> ShapeProperties:
        center = self.context._value_state(
            ops.volume_center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.volume_properties.center",
        )
        mass = self.context._value_state(
            ops.volume_mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.volume_properties.mass",
        )
        return ShapeProperties(
            Point3._from_state(self.context, center),
            Scalar._from_state(self.context, mass),
        )

    def fill(self) -> Face:
        from .face_constructors import _fill_shape

        return _fill_shape(self)

    def extrude(
        self,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        from .sweeps import extrude

        return extrude(self, vec, center)

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
        from .sweeps import revol

        return revol(self, r, yaw)

    def fillet(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | ShapeList[Edge] | Sequence[Edge] | None = None,
    ) -> Shape:
        from .modeling import fillet

        return fillet(self, r, refs)

    def chamfer(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | ShapeList[Edge] | Sequence[Edge] | None = None,
    ) -> Shape:
        from .modeling import chamfer

        return chamfer(self, r, refs)

    def fillet2d(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Face:
        from .modeling import fillet2d

        if not isinstance(self, Face):
            raise TypeError("fillet2d expects Face")
        return fillet2d(self, r, refs)

    def chamfer2d(
        self,
        r: ScalarInput,
        refs: Sequence[Point3] | None = None,
    ) -> Face:
        from .modeling import chamfer2d

        if not isinstance(self, Face):
            raise TypeError("chamfer2d expects Face")
        return chamfer2d(self, r, refs)

    def restore_shapetype(self) -> Shape:
        """Recover a precise topology handle when exactly one subtype exists."""
        from .modeling import restore_shapetype

        return restore_shapetype(self)

    def offset(self, distance: ScalarInput, /) -> Shape:
        from .modeling import offset

        return offset(self, distance)

    def unify(self: ShapeT) -> ShapeT:
        from .modeling import unify

        return cast(ShapeT, unify(self))

    def validate(
        self,
        *,
        exact: bool = False,
        parallel: bool = False,
    ) -> ValidationReport:
        from .modeling import validate

        return validate(self, exact=exact, parallel=parallel)

    def is_valid(
        self,
        *,
        exact: bool = False,
        parallel: bool = False,
    ) -> bool:
        from .modeling import is_valid

        return is_valid(self, exact=exact, parallel=parallel)

    def assert_valid(
        self: ShapeT,
        *,
        exact: bool = False,
        parallel: bool = False,
    ) -> ShapeT:
        from .modeling import assert_valid

        return assert_valid(self, exact=exact, parallel=parallel)

    def clean(self: ShapeT) -> ShapeT:
        from .modeling import clean

        return cast(ShapeT, clean(self))

    def heal(
        self: ShapeT,
        tolerance: float = 1e-7,
        max_tolerance: float = 1e-3,
    ) -> ShapeT:
        from .modeling import heal

        return cast(ShapeT, heal(self, tolerance, max_tolerance))

    def near_vertex(self, point: Point3, /) -> Vertex:
        from .modeling import near_vertex

        return near_vertex(self, point)

    def near_edge(self, point: Point3, /) -> Edge:
        from .modeling import near_edge

        return near_edge(self, point)

    def near_wire(self, point: Point3, /) -> Wire:
        from .modeling import near_wire

        return near_wire(self, point)

    def near_face(self, point: Point3, /) -> Face:
        from .modeling import near_face

        return near_face(self, point)

    def near_shell(self, point: Point3, /) -> Shell:
        from .modeling import near_shell

        return near_shell(self, point)

    def near_solid(self, point: Point3, /) -> Solid:
        from .modeling import near_solid

        return near_solid(self, point)

    def near_compsolid(self, point: Point3, /) -> CompSolid:
        from .modeling import near_compsolid

        return near_compsolid(self, point)

    def near_compound(self, point: Point3, /) -> Compound:
        from .modeling import near_compound

        return near_compound(self, point)

    def edges(self) -> ShapeList[Edge]:
        return self._topology_query(
            ops.edges,
            sequence_spec=_EDGE_SEQUENCE_SPEC,
            item_type=Edge,
            item_spec=EDGE_SPEC,
            operation_id="zencad.typed.shape.edges",
        )

    def wires(self) -> ShapeList[Wire]:
        return self._topology_query(
            ops.wires,
            sequence_spec=_WIRE_SEQUENCE_SPEC,
            item_type=Wire,
            item_spec=WIRE_SPEC,
            operation_id="zencad.typed.shape.wires",
        )

    def faces(self) -> ShapeList[Face]:
        return self._topology_query(
            ops.faces,
            sequence_spec=_FACE_SEQUENCE_SPEC,
            item_type=Face,
            item_spec=FACE_SPEC,
            operation_id="zencad.typed.shape.faces",
        )

    def shells(self) -> ShapeList[Shell]:
        return self._topology_query(
            ops.shells,
            sequence_spec=_SHELL_SEQUENCE_SPEC,
            item_type=Shell,
            item_spec=SHELL_SPEC,
            operation_id="zencad.typed.shape.shells",
        )

    def solids(self) -> ShapeList[Solid]:
        return self._topology_query(
            ops.solids,
            sequence_spec=_SOLID_SEQUENCE_SPEC,
            item_type=Solid,
            item_spec=SOLID_SPEC,
            operation_id="zencad.typed.shape.solids",
        )

    def compounds(self) -> ShapeList[Compound]:
        return self._topology_query(
            ops.compounds,
            sequence_spec=_COMPOUND_SEQUENCE_SPEC,
            item_type=Compound,
            item_spec=COMPOUND_SPEC,
            operation_id="zencad.typed.shape.compounds",
        )

    def compsolids(self) -> ShapeList[CompSolid]:
        return self._topology_query(
            ops.compsolids,
            sequence_spec=_COMPSOLID_SEQUENCE_SPEC,
            item_type=CompSolid,
            item_spec=COMPSOLID_SPEC,
            operation_id="zencad.typed.shape.compsolids",
        )

    def mass(self) -> Scalar:
        state = self.context._value_state(
            ops.mass,
            result=SCALAR_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.mass",
        )
        return Scalar._from_state(self.context, state)

    def center(self) -> Point3:
        state = self.context._value_state(
            ops.center,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.shape.center",
        )
        return Point3._from_state(self.context, state)

    def boundbox(self) -> BoundaryBox:
        """Return graph-preserving axis-aligned bounds for this shape."""
        from .modeling import boundbox

        return boundbox(self)

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
        from .meshes import to_mesh

        return to_mesh(
            self,
            linear_deflection,
            angular_deflection,
            crease_angle=crease_angle,
            relative=relative,
            parallel=parallel,
            weld_tolerance=weld_tolerance,
        )

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
        state = self.context._value_state(
            ops.vertex_point,
            result=POINT3_SPEC,
            args=(self._state,),
            operation_id="zencad.typed.vertex.point",
        )
        return Point3._from_state(self.context, state)

    def native(self) -> TopoDS_Vertex:
        return as_vertex(super().native())


class Edge(Shape):
    __slots__ = ()
    _result_spec = EDGE_SPEC

    def curve(self) -> Curve:
        from .curve_constructors import _edge_curve

        return _edge_curve(self)

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
        from .surface_topology import _face_surface

        return _face_surface(self)

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
        from .meshes import triangulate

        return triangulate(
            self,
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
        from .modeling import thicksolid

        return thicksolid(self, thickness, references)

    def shapefix_solid(self) -> Solid:
        from .modeling import shapefix_solid

        return shapefix_solid(self)

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


_GEOMETRY_TYPE_SEQUENCE_SPEC = cast(
    ResultSpec[tuple[str, ...]],
    ResultSpec.for_type(
        tuple,
        type_id="zencad.typed.Sequence[GeomType].v1",
        validator=lambda values: all(
            isinstance(value, str) and value in {kind.value for kind in GeomType}
            for value in values
        ),
    ),
)


class ShapeList(Generic[ShapeHandleT]):
    """Composable typed topology collection backed by an expression node."""

    __slots__ = (
        "_expression",
        "_item_spec",
        "_item_type",
        "_operation_id",
        "_context",
        "_sequence_spec",
    )

    def __init__(
        self,
        context: Context,
        expression: Expression[tuple[ResolvedShape, ...]],
        *,
        sequence_spec: ResultSpec[tuple[ResolvedShape, ...]],
        item_type: type[ShapeHandleT],
        item_spec: ResultSpec[ResolvedShape],
        operation_id: str,
    ) -> None:
        self._context = context
        self._expression = expression
        self._sequence_spec = sequence_spec
        self._item_type = item_type
        self._item_spec = item_spec
        self._operation_id = operation_id

    @property
    def context(self) -> Context:
        return self._context

    def _sequence(
        self,
        operation: Callable[..., tuple[ResolvedShape, ...]],
        *args: object,
        operation_id: str,
    ) -> ShapeList[ShapeHandleT]:
        expression = self._context._expression(
            operation,
            result=self._sequence_spec,
            args=(self._expression, *args),
            operation_id=operation_id,
            cacheable=False,
        )
        return ShapeList(
            self._context,
            expression,
            sequence_spec=self._sequence_spec,
            item_type=self._item_type,
            item_spec=self._item_spec,
            operation_id=f"{operation_id}.item",
        )

    def _item(
        self,
        operation: Callable[..., ResolvedShape],
        *args: object,
        operation_id: str,
    ) -> ShapeHandleT:
        expression = self._context._expression(
            operation,
            result=self._item_spec,
            args=(self._expression, *args),
            operation_id=operation_id,
        )
        return self._item_type._from_state(self._context, expression)

    @overload
    def __getitem__(self, index: int) -> ShapeHandleT: ...

    @overload
    def __getitem__(self, index: slice) -> ShapeList[ShapeHandleT]: ...

    def __getitem__(self, index: int | slice) -> ShapeHandleT | ShapeList[ShapeHandleT]:
        if isinstance(index, slice):
            for value in (index.start, index.stop, index.step):
                if value is not None and (
                    not isinstance(value, int) or isinstance(value, bool)
                ):
                    raise TypeError("ShapeList slice bounds must be integers")
            return self._sequence(
                selector_ops.sequence_slice,
                index.start,
                index.stop,
                index.step,
                operation_id="zencad.typed.shapelist.slice",
            )
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("ShapeList indices must be integers or slices")
        return self._item(
            ops.sequence_item,
            index,
            operation_id=self._operation_id,
        )

    def __len__(self) -> int:
        return len(self._context._resolve(self._expression))

    def __iter__(self) -> Iterator[ShapeHandleT]:
        for index in range(len(self)):
            yield self[index]

    def filter_by(
        self,
        criterion: Axis | GeomType | Plane,
        *,
        tolerance: float = 1e-7,
    ) -> ShapeList[ShapeHandleT]:
        """Filter by geometry kind, principal direction, or center plane."""

        if isinstance(criterion, GeomType):
            return self._sequence(
                selector_ops.filter_geometry_type,
                criterion.value,
                operation_id="zencad.typed.shapelist.filter.geometry_type",
            )
        if isinstance(criterion, Axis):
            return self._filter_direction(
                criterion.direction,
                tolerance=tolerance,
                planar_only=False,
            )
        if isinstance(criterion, Plane):
            return self.filter_by_position(criterion, tolerance=tolerance)
        raise TypeError("filter_by expects Axis, GeomType, or Plane")

    def _filter_direction(
        self,
        direction: Sequence[float],
        *,
        tolerance: float,
        planar_only: bool,
    ) -> ShapeList[ShapeHandleT]:
        values = _selector_direction(direction)
        return self._sequence(
            selector_ops.filter_direction,
            values,
            _selector_tolerance(tolerance, "direction tolerance"),
            planar_only,
            operation_id="zencad.typed.shapelist.filter.direction",
        )

    def normal_to(
        self,
        direction: Axis | Sequence[float],
        *,
        tolerance: float = 1e-7,
    ) -> ShapeList[ShapeHandleT]:
        """Keep planar faces whose normal is parallel to ``direction``."""

        values = direction.direction if isinstance(direction, Axis) else direction
        return self._filter_direction(
            values,
            tolerance=tolerance,
            planar_only=True,
        )

    def planar(self) -> ShapeList[ShapeHandleT]:
        return self.filter_by(GeomType.PLANE)

    def filter_by_position(
        self,
        criterion: Axis | Plane,
        position: ScalarInput = 0,
        *,
        tolerance: float = 1e-7,
    ) -> ShapeList[ShapeHandleT]:
        """Keep shapes whose center lies on an axis coordinate or plane."""

        with using_context(self._context):
            if isinstance(criterion, Axis):
                direction = criterion.direction
                origin = point3(*(component * position for component in direction))
                normal = direction
            elif isinstance(criterion, Plane):
                if isinstance(position, Scalar) or position != 0:
                    raise TypeError("position is only valid with an Axis criterion")
                origin = point3(criterion.origin)
                normal = criterion.normal
            else:
                raise TypeError("filter_by_position expects Axis or Plane")
        return self._sequence(
            selector_ops.filter_position,
            origin._state,
            _selector_direction(normal),
            _selector_tolerance(tolerance, "position tolerance"),
            operation_id="zencad.typed.shapelist.filter.position",
        )

    def sort_by(
        self,
        criterion: Axis | Plane,
        *,
        reverse: bool = False,
    ) -> ShapeList[ShapeHandleT]:
        """Stable-sort shapes by center projection on an axis or plane normal."""

        if isinstance(criterion, Axis):
            direction = criterion.direction
        elif isinstance(criterion, Plane):
            direction = criterion.normal
        else:
            raise TypeError("sort_by expects Axis or Plane")
        return self._sequence(
            selector_ops.sort_axis,
            _selector_direction(direction),
            _selector_reverse(reverse),
            operation_id="zencad.typed.shapelist.sort.axis",
        )

    def sort_by_distance(
        self,
        point: Point3 | Sequence[ScalarInput],
        *,
        reverse: bool = False,
    ) -> ShapeList[ShapeHandleT]:
        """Stable-sort by the exact minimum OCCT distance to ``point``."""

        with using_context(self._context):
            query = point3(point)
        return self._sequence(
            selector_ops.sort_distance,
            query._state,
            _selector_reverse(reverse),
            operation_id="zencad.typed.shapelist.sort.distance",
        )

    def longer_than(self, threshold: ScalarInput) -> ShapeList[ShapeHandleT]:
        """Keep edges or wires whose linear measure exceeds ``threshold``."""

        if not issubclass(self._item_type, (Edge, Wire)):
            raise TypeError("longer_than is only defined for Edge and Wire ShapeLists")
        return self._sequence(
            selector_ops.filter_measure,
            _scalar_state(self._context, threshold),
            operation_id="zencad.typed.shapelist.filter.longer_than",
        )

    def largest(self) -> ShapeHandleT:
        """Return the first largest shape; an empty list fails on evaluation."""

        return self._item(
            selector_ops.largest,
            operation_id="zencad.typed.shapelist.largest",
        )

    def only(self) -> ShapeHandleT:
        """Return the sole item; any other cardinality fails on evaluation."""

        return self._item(
            selector_ops.only,
            operation_id="zencad.typed.shapelist.only",
        )

    def geometry_types(self) -> tuple[GeomType, ...]:
        state = self._context._value_state(
            selector_ops.sequence_geometry_types,
            result=_GEOMETRY_TYPE_SEQUENCE_SPEC,
            args=(self._expression,),
            operation_id="zencad.typed.shapelist.geometry_types",
        )
        values = self._context._resolve(state) if isinstance(state, Expression) else state
        return tuple(GeomType(value) for value in values)

    def group_by(
        self,
        criterion: type[GeomType],
    ) -> dict[GeomType, ShapeList[ShapeHandleT]]:
        """Group by geometry kind in stable first-occurrence order."""

        if criterion is not GeomType:
            raise TypeError("group_by currently accepts the GeomType criterion")
        return {
            kind: self.filter_by(kind)
            for kind in dict.fromkeys(self.geometry_types())
        }


DeferredSequence = ShapeList


def _selector_direction(value: Sequence[float]) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)):
        raise TypeError("selector direction must contain three numeric coordinates")
    try:
        values = tuple(float(item) for item in value)
    except (TypeError, ValueError) as error:
        raise TypeError(
            "selector direction must contain three numeric coordinates"
        ) from error
    if len(values) != 3:
        raise TypeError("selector direction must contain three numeric coordinates")
    return values


def _selector_tolerance(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def _selector_reverse(value: bool) -> bool:
    if not isinstance(value, bool):
        raise TypeError("reverse must be bool")
    return value
