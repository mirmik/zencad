"""Typed topology modeling and nearest-part queries declared at module level."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TypeVar, overload

from evalcache import Expression, ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.validation import (
    ShapeValidationError,
    ValidationReport,
)
from zencad.operation import (
    operation,
    resolve_context,
)

from . import _bound_operations as bound_ops
from . import _operations as ops
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .curves import Curve
from .records import CurveProjection
from .topology import (
    COMPOUND_SPEC,
    COMPSOLID_SPEC,
    EDGE_SPEC,
    FACE_SPEC,
    SHAPE_SPEC,
    SHELL_SPEC,
    SOLID_SPEC,
    VERTEX_SPEC,
    WIRE_SPEC,
    Compound,
    CompSolid,
    Edge,
    Face,
    Shape,
    Shell,
    Solid,
    Vertex,
    Wire,
)
from .values import Point3, Vector3


DraftPlaneInput = (
    Face
    | tuple[
        Point3 | Sequence[float],
        Vector3 | Sequence[float],
    ]
)
RoundedReference = Point3 | Edge
ShapeModelT = TypeVar("ShapeModelT", bound=Shape)
VALIDATION_REPORT_SPEC = ResultSpec.for_type(
    ValidationReport,
    type_id="zencad.typed.ValidationReport.v1",
)


def _rounded_values(
    shape: Shape,
    radius: float,
    references: Iterable[RoundedReference] | None,
    name: str,
) -> tuple[ResolvedShape, float, tuple[object, ...] | None]:
    _require_shape(shape, name)
    selected = _require_references(references, name)
    if isinstance(shape, Face) and selected and isinstance(selected[0], Edge):
        raise TypeError(f"{name} on a Face accepts Point3 references, not Edges")
    return (
        shape._legacy(),
        radius,
        None
        if selected is None
        else tuple(
            reference._legacy()
            if isinstance(reference, Edge)
            else reference._resolved()
            for reference in selected
        ),
    )


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.fillet",
    operation_version="1",
)
def fillet(
    shape: Shape,
    radius: float,
    references: Iterable[RoundedReference] | None = None,
    /,
) -> Shape:
    return Shape(
        ops.fillet_shape(*_rounded_values(shape, radius, references, "fillet"))
    )


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.chamfer",
    operation_version="1",
)
def chamfer(
    shape: Shape,
    radius: float,
    references: Iterable[RoundedReference] | None = None,
    /,
) -> Shape:
    return Shape(
        ops.chamfer_shape(*_rounded_values(shape, radius, references, "chamfer"))
    )


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.fillet2d",
    operation_version="1",
)
def fillet2d(
    shape: Face,
    radius: float,
    references: Sequence[Point3] | None = None,
    /,
) -> Face:
    _require_face(shape, "fillet2d")
    return Face(
        ops.fillet2d_shape(*_rounded_values(shape, radius, references, "fillet2d"))
    )


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.chamfer2d",
    operation_version="1",
)
def chamfer2d(
    shape: Face,
    radius: float,
    references: Sequence[Point3] | None = None,
    /,
) -> Face:
    _require_face(shape, "chamfer2d")
    return Face(
        ops.chamfer2d_shape(*_rounded_values(shape, radius, references, "chamfer2d"))
    )


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.draft",
    operation_version="1",
)
def draft(
    body: Solid,
    faces: Face | Iterable[Face],
    angle: float,
    direction: Vector3 | Sequence[float] = (0, 0, 1),
    neutral: DraftPlaneInput | None = None,
) -> Solid:
    """Taper faces; positive angle removes material along pull direction."""

    _require_solid(body, "draft")
    selected = _require_draft_faces(faces)
    pull_direction = (
        direction if isinstance(direction, Vector3) else Vector3(tuple(direction))
    )
    if neutral is not None:
        if isinstance(neutral, Face):
            pass
        elif isinstance(neutral, Sequence) and not isinstance(neutral, (str, bytes)):
            if len(neutral) != 2:
                raise TypeError("draft neutral must be (origin, normal)")
        else:
            raise TypeError("draft neutral must be a planar Face or (origin, normal)")
    return Solid(
        ops.draft_shape(
            body._legacy(),
            tuple(face._legacy() for face in selected),
            angle,
            pull_direction._resolved(),
            _resolved_draft_plane(neutral),
        )
    )


def _resolved_draft_plane(neutral: DraftPlaneInput | None) -> object:
    if neutral is None:
        return None
    if isinstance(neutral, Face):
        return neutral._legacy()
    origin, normal = neutral
    return (
        origin._resolved() if isinstance(origin, Point3) else tuple(origin),
        normal._resolved() if isinstance(normal, Vector3) else tuple(normal),
    )


@overload
def restore_shapetype(shape: Solid, /) -> Solid: ...


@overload
def restore_shapetype(shape: Shell, /) -> Shell: ...


@overload
def restore_shapetype(shape: Face, /) -> Face: ...


@overload
def restore_shapetype(shape: Wire, /) -> Wire: ...


@overload
def restore_shapetype(shape: Edge, /) -> Edge: ...


@overload
def restore_shapetype(shape: Shape, /) -> Shape: ...


def restore_shapetype(shape: Shape, /) -> Shape:
    """Recover a precise topology handle when exactly one subtype exists."""

    _require_shape(shape, "restore_shapetype")
    candidates = (
        shape.solids(),
        shape.shells(),
        shape.faces(),
        shape.wires(),
        shape.edges(),
    )
    for candidates_of_kind in candidates:
        if len(candidates_of_kind) == 1:
            return candidates_of_kind[0]
    return shape


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.sew.wire",
    operation_version="1",
)
def _sew_wire(
    shapes: Sequence[Edge | Wire],
    sort: bool,
    /,
) -> Wire:
    _require_bool(sort, "sew sort")
    values = _require_wire_parts(shapes, "sew")
    return Wire(ops.sew_wire(tuple(shape._legacy() for shape in values), sort))


@operation(
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.sew.shell",
    operation_version="1",
)
def _sew_shell(
    shapes: Sequence[Face | Shell],
    /,
) -> Shell:
    values = _require_shell_parts(shapes, "sew")
    return Shell(ops.sew_shell(tuple(shape._legacy() for shape in values)))


@overload
def sew(
    shapes: Sequence[Edge | Wire],
    sort: bool = True,
    /,
) -> Wire: ...


@overload
def sew(
    shapes: Sequence[Face | Shell],
    sort: bool = True,
    /,
) -> Shell: ...


def sew(
    shapes: Sequence[Edge | Wire] | Sequence[Face | Shell],
    sort: bool = True,
    /,
) -> Wire | Shell:
    _require_bool(sort, "sew sort")
    if isinstance(shapes, (str, bytes)) or not isinstance(shapes, Sequence):
        raise TypeError("sew expects a sequence of topology handles")
    values = tuple(shapes)
    if not values:
        raise ValueError("sew requires at least one topology handle")
    if all(isinstance(shape, (Edge, Wire)) for shape in values):
        return _sew_wire(values, sort)
    if all(isinstance(shape, (Face, Shell)) for shape in values):
        return _sew_shell(values)
    raise TypeError("sew operands must all be Edge/Wire or all be Face/Shell")


@operation(
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.offset",
    operation_version="1",
)
def offset(shape: Shape, distance: float, /) -> Shape:
    _require_shape(shape, "offset")
    return Shape(ops.offset_shape(shape._legacy(), distance))


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.thicksolid",
    operation_version="1",
)
def thicksolid(
    shape: Solid,
    thickness: float,
    references: Sequence[Point3],
    /,
) -> Solid:
    _require_solid(shape, "thicksolid")
    resolved_references = _require_references(references, "thicksolid")
    assert resolved_references is not None
    return Solid(
        ops.thicksolid_shape(
            shape._legacy(),
            thickness,
            tuple(reference._resolved() for reference in resolved_references),
        )
    )


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.shapefix",
    operation_version="1",
)
def shapefix_solid(shape: Solid, /) -> Solid:
    _require_solid(shape, "shapefix_solid")
    return Solid(ops.shapefix_solid_shape(shape._legacy()))


def _shape_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Shape]:
    del kwargs
    return type(args[0]) if args and isinstance(args[0], Shape) else Shape


def _shape_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    del kwargs
    return args[0]._result_spec if args and isinstance(args[0], Shape) else SHAPE_SPEC


@overload
def unify(shape: Solid, /) -> Solid: ...


@overload
def unify(shape: Shell, /) -> Shell: ...


@overload
def unify(shape: Face, /) -> Face: ...


@overload
def unify(shape: Wire, /) -> Wire: ...


@overload
def unify(shape: Edge, /) -> Edge: ...


@overload
def unify(shape: Vertex, /) -> Vertex: ...


@overload
def unify(shape: CompSolid, /) -> CompSolid: ...


@overload
def unify(shape: Compound, /) -> Compound: ...


@overload
def unify(shape: Shape, /) -> Shape: ...


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.unify",
    operation_version="1",
)
def unify(shape: Shape, /) -> Shape:
    _require_shape(shape, "unify")
    return type(shape)(ops.unify_shape(shape._legacy()))


def validate(
    shape: Shape,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> ValidationReport:
    """Materialize a shape and return structured, non-mutating diagnostics."""

    _require_shape(shape, "validate")
    _require_bool(exact, "validate exact")
    _require_bool(parallel, "validate parallel")
    state = shape.context._value_state(
        ops.validate_shape,
        result=VALIDATION_REPORT_SPEC,
        args=(shape._state, exact, parallel),
        operation_id="zencad.typed.shape.validate",
    )
    if isinstance(state, Expression):
        return shape.context._resolve(state)
    return state


def is_valid(
    shape: Shape,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> bool:
    return validate(shape, exact=exact, parallel=parallel).valid


def assert_valid(
    shape: ShapeModelT,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> ShapeModelT:
    report = validate(shape, exact=exact, parallel=parallel)
    if not report.valid:
        raise ShapeValidationError(report)
    return shape


@overload
def clean(shape: Solid, /) -> Solid: ...


@overload
def clean(shape: Shell, /) -> Shell: ...


@overload
def clean(shape: Face, /) -> Face: ...


@overload
def clean(shape: Wire, /) -> Wire: ...


@overload
def clean(shape: Edge, /) -> Edge: ...


@overload
def clean(shape: Vertex, /) -> Vertex: ...


@overload
def clean(shape: CompSolid, /) -> CompSolid: ...


@overload
def clean(shape: Compound, /) -> Compound: ...


@overload
def clean(shape: Shape, /) -> Shape: ...


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.clean",
    operation_version="1",
)
def clean(shape: Shape, /) -> Shape:
    _require_shape(shape, "clean")
    return type(shape)(ops.clean_shape(shape._legacy()))


@overload
def heal(
    shape: Solid, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> Solid: ...


@overload
def heal(
    shape: Shell, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> Shell: ...


@overload
def heal(shape: Face, tolerance: float = 1e-7, max_tolerance: float = 1e-3) -> Face: ...


@overload
def heal(shape: Wire, tolerance: float = 1e-7, max_tolerance: float = 1e-3) -> Wire: ...


@overload
def heal(shape: Edge, tolerance: float = 1e-7, max_tolerance: float = 1e-3) -> Edge: ...


@overload
def heal(
    shape: Vertex, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> Vertex: ...


@overload
def heal(
    shape: CompSolid, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> CompSolid: ...


@overload
def heal(
    shape: Compound, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> Compound: ...


@overload
def heal(
    shape: Shape, tolerance: float = 1e-7, max_tolerance: float = 1e-3
) -> Shape: ...


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.heal",
    operation_version="1",
)
def heal(
    shape: Shape,
    tolerance: float = 1e-7,
    max_tolerance: float = 1e-3,
) -> Shape:
    _require_shape(shape, "heal")
    return type(shape)(ops.heal_shape(shape._legacy(), tolerance, max_tolerance))


@operation(
    result=VERTEX_SPEC,
    returns=Vertex,
    operation_id="zencad.typed.shape.near_vertex",
    operation_version="1",
)
def near_vertex(shape: Shape, point: Point3, /) -> Vertex:
    resolved_shape, resolved_point = _near_values(shape, point, "vertex")
    return Vertex(ops.near_vertex(resolved_shape, resolved_point))


@operation(
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.shape.near_edge",
    operation_version="1",
)
def near_edge(shape: Shape, point: Point3, /) -> Edge:
    resolved_shape, resolved_point = _near_values(shape, point, "edge")
    return Edge(ops.near_edge(resolved_shape, resolved_point))


@operation(
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.shape.near_wire",
    operation_version="1",
)
def near_wire(shape: Shape, point: Point3, /) -> Wire:
    resolved_shape, resolved_point = _near_values(shape, point, "wire")
    return Wire(ops.near_wire(resolved_shape, resolved_point))


@operation(
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.near_face",
    operation_version="1",
)
def near_face(shape: Shape, point: Point3, /) -> Face:
    resolved_shape, resolved_point = _near_values(shape, point, "face")
    return Face(ops.near_face(resolved_shape, resolved_point))


@operation(
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.shape.near_shell",
    operation_version="1",
)
def near_shell(shape: Shape, point: Point3, /) -> Shell:
    resolved_shape, resolved_point = _near_values(shape, point, "shell")
    return Shell(ops.near_shell(resolved_shape, resolved_point))


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.shape.near_solid",
    operation_version="1",
)
def near_solid(shape: Shape, point: Point3, /) -> Solid:
    resolved_shape, resolved_point = _near_values(shape, point, "solid")
    return Solid(ops.near_solid(resolved_shape, resolved_point))


@operation(
    result=COMPSOLID_SPEC,
    returns=CompSolid,
    operation_id="zencad.typed.shape.near_compsolid",
    operation_version="1",
)
def near_compsolid(shape: Shape, point: Point3, /) -> CompSolid:
    resolved_shape, resolved_point = _near_values(shape, point, "compsolid")
    return CompSolid(ops.near_compsolid(resolved_shape, resolved_point))


@operation(
    result=COMPOUND_SPEC,
    returns=Compound,
    operation_id="zencad.typed.shape.near_compound",
    operation_version="1",
)
def near_compound(shape: Shape, point: Point3, /) -> Compound:
    resolved_shape, resolved_point = _near_values(shape, point, "compound")
    return Compound(ops.near_compound(resolved_shape, resolved_point))


def project_point_on_curve(
    point: Point3,
    target: Curve | Edge,
    /,
) -> CurveProjection:
    if not isinstance(point, Point3):
        raise TypeError("project_point_on_curve point must be Point3")
    if not isinstance(target, (Curve, Edge)):
        raise TypeError("project_point_on_curve target must be Curve or Edge")
    resolve_context(point, target)
    curve = target.curve() if isinstance(target, Edge) else target
    parameter = curve.lower_distance_parameter(point)
    projected = curve.point(parameter)
    return CurveProjection(projected, parameter, (projected - point).length())


def project(point: Point3, target: Curve | Edge, /) -> CurveProjection:
    return project_point_on_curve(point, target)


@operation(
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.shape.boundbox",
    operation_version="1",
)
def boundbox(shape: Shape, /) -> BoundaryBox:
    _require_shape(shape, "boundbox")
    return BoundaryBox(bound_ops.shape_boundary_box(shape._legacy()))


def _near_values(shape: Shape, point: Point3, name: str):
    _require_shape(shape, f"near_{name}")
    if not isinstance(point, Point3):
        raise TypeError(f"near_{name} expects Point3")
    return (shape._legacy(), point._resolved())


def _require_references(
    references: Iterable[RoundedReference] | None,
    name: str,
) -> tuple[RoundedReference, ...] | None:
    if references is None:
        return None
    if isinstance(references, (str, bytes)):
        raise TypeError(f"{name} references must be Point3 values or Edges")
    try:
        values = tuple(references)
    except TypeError as error:
        raise TypeError(f"{name} references must be Point3 values or Edges") from error
    if not values:
        raise ValueError(f"{name} references must not be empty")
    if not (
        all(isinstance(value, Point3) for value in values)
        or all(isinstance(value, Edge) for value in values)
    ):
        raise TypeError(f"{name} references must be all Point3 values or all Edges")
    resolve_context(values)
    return values


def _require_draft_faces(faces: Face | Iterable[Face]) -> tuple[Face, ...]:
    if isinstance(faces, Face):
        values = (faces,)
    elif isinstance(faces, (str, bytes)):
        raise TypeError("draft faces must be a Face or an iterable of Faces")
    else:
        try:
            values = tuple(faces)
        except TypeError as error:
            raise TypeError(
                "draft faces must be a Face or an iterable of Faces"
            ) from error
    if not values:
        raise ValueError("draft requires at least one Face")
    if not all(isinstance(face, Face) for face in values):
        raise TypeError("draft faces must contain only Face handles")
    resolve_context(values)
    return values


def _require_wire_parts(
    shapes: Sequence[Edge | Wire],
    name: str,
) -> tuple[Edge | Wire, ...]:
    values = tuple(shapes)
    if not values:
        raise ValueError(f"{name} requires at least one topology handle")
    if not all(isinstance(shape, (Edge, Wire)) for shape in values):
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    resolve_context(values)
    return values


def _require_shell_parts(
    shapes: Sequence[Face | Shell],
    name: str,
) -> tuple[Face | Shell, ...]:
    values = tuple(shapes)
    if not values:
        raise ValueError(f"{name} requires at least one topology handle")
    if not all(isinstance(shape, (Face, Shell)) for shape in values):
        raise TypeError(f"{name} accepts only Face or Shell handles")
    resolve_context(values)
    return values


def _require_shape(shape: object, name: str) -> None:
    if not isinstance(shape, Shape):
        raise TypeError(f"{name} expects Shape")


def _require_face(shape: object, name: str) -> None:
    if not isinstance(shape, Face):
        raise TypeError(f"{name} expects Face")


def _require_solid(shape: object, name: str) -> None:
    if not isinstance(shape, Solid):
        raise TypeError(f"{name} expects Solid")


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


__all__ = [
    "assert_valid",
    "boundbox",
    "chamfer",
    "chamfer2d",
    "draft",
    "fillet",
    "fillet2d",
    "clean",
    "heal",
    "is_valid",
    "near_compound",
    "near_compsolid",
    "near_edge",
    "near_face",
    "near_shell",
    "near_solid",
    "near_vertex",
    "near_wire",
    "offset",
    "project",
    "project_point_on_curve",
    "restore_shapetype",
    "sew",
    "shapefix_solid",
    "thicksolid",
    "unify",
    "validate",
]
