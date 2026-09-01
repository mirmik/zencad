"""Typed topology modeling and nearest-part queries declared at module level."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import overload

from evalcache import ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.operation import (
    OperationArguments,
    arguments,
    operation,
    resolve_runtime,
    using_runtime,
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
from .values import Point3, ScalarInput, Vector3, _scalar_state, vector3


DraftPlaneInput = Face | tuple[
    Point3 | Sequence[ScalarInput],
    Vector3 | Sequence[ScalarInput],
]


def _rounded_arguments(
    shape: Shape,
    radius: ScalarInput,
    references: Sequence[Point3] | None,
    name: str,
) -> OperationArguments:
    _require_shape(shape, name)
    runtime = resolve_runtime(shape, radius, references)
    return arguments(
        shape,
        _scalar_state(runtime, radius),
        _require_references(references, name),
    )


@operation(
    backend=ops.fillet_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.fillet",
    operation_version="1",
)
def fillet(
    shape: Shape,
    radius: ScalarInput,
    references: Sequence[Point3] | None = None,
    /,
) -> OperationArguments:
    return _rounded_arguments(shape, radius, references, "fillet")


@operation(
    backend=ops.chamfer_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.chamfer",
    operation_version="1",
)
def chamfer(
    shape: Shape,
    radius: ScalarInput,
    references: Sequence[Point3] | None = None,
    /,
) -> OperationArguments:
    return _rounded_arguments(shape, radius, references, "chamfer")


@operation(
    backend=ops.fillet2d_shape,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.fillet2d",
    operation_version="1",
)
def fillet2d(
    shape: Face,
    radius: ScalarInput,
    references: Sequence[Point3] | None = None,
    /,
) -> OperationArguments:
    _require_face(shape, "fillet2d")
    return _rounded_arguments(shape, radius, references, "fillet2d")


@operation(
    backend=ops.chamfer2d_shape,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.chamfer2d",
    operation_version="1",
)
def chamfer2d(
    shape: Face,
    radius: ScalarInput,
    references: Sequence[Point3] | None = None,
    /,
) -> OperationArguments:
    _require_face(shape, "chamfer2d")
    return _rounded_arguments(shape, radius, references, "chamfer2d")


@operation(
    backend=ops.draft_shape,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.draft",
    operation_version="1",
)
def draft(
    body: Solid,
    faces: Face | Iterable[Face],
    angle: ScalarInput,
    direction: Vector3 | Sequence[ScalarInput] = (0, 0, 1),
    neutral: DraftPlaneInput | None = None,
) -> OperationArguments:
    """Taper faces; positive angle removes material along pull direction."""

    _require_solid(body, "draft")
    selected = _require_draft_faces(faces)
    runtime = resolve_runtime(body, selected, angle, direction, neutral)
    with using_runtime(runtime):
        pull_direction = vector3(direction)
    if neutral is not None:
        if isinstance(neutral, Face):
            pass
        elif isinstance(neutral, Sequence) and not isinstance(neutral, (str, bytes)):
            if len(neutral) != 2:
                raise TypeError("draft neutral must be (origin, normal)")
        else:
            raise TypeError("draft neutral must be a planar Face or (origin, normal)")
    return arguments(
        body,
        selected,
        _scalar_state(runtime, angle),
        pull_direction,
        neutral,
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
    backend=ops.sew_wire,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.sew.wire",
    operation_version="1",
)
def _sew_wire(
    shapes: Sequence[Edge | Wire],
    sort: bool,
    /,
) -> OperationArguments:
    _require_bool(sort, "sew sort")
    return arguments(_require_wire_parts(shapes, "sew"), sort)


@operation(
    backend=ops.sew_shell,
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.sew.shell",
    operation_version="1",
)
def _sew_shell(
    shapes: Sequence[Face | Shell],
    /,
) -> OperationArguments:
    return arguments(_require_shell_parts(shapes, "sew"))


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
    backend=ops.offset_shape,
    result=SHAPE_SPEC,
    returns=Shape,
    operation_id="zencad.typed.shape.offset",
    operation_version="1",
)
def offset(shape: Shape, distance: ScalarInput, /) -> OperationArguments:
    _require_shape(shape, "offset")
    runtime = resolve_runtime(shape, distance)
    return arguments(shape, _scalar_state(runtime, distance))


@operation(
    backend=ops.thicksolid_shape,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.thicksolid",
    operation_version="1",
)
def thicksolid(
    shape: Solid,
    thickness: ScalarInput,
    references: Sequence[Point3],
    /,
) -> OperationArguments:
    _require_solid(shape, "thicksolid")
    runtime = resolve_runtime(shape, thickness, references)
    resolved_references = _require_references(references, "thicksolid")
    assert resolved_references is not None
    return arguments(
        shape,
        _scalar_state(runtime, thickness),
        resolved_references,
    )


@operation(
    backend=ops.shapefix_solid_shape,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.solid.shapefix",
    operation_version="1",
)
def shapefix_solid(shape: Solid, /) -> OperationArguments:
    _require_solid(shape, "shapefix_solid")
    return arguments(shape)


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
    backend=ops.unify_shape,
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.unify",
    operation_version="1",
)
def unify(shape: Shape, /) -> OperationArguments:
    _require_shape(shape, "unify")
    return arguments(shape)


@operation(
    backend=ops.near_vertex,
    result=VERTEX_SPEC,
    returns=Vertex,
    operation_id="zencad.typed.shape.near_vertex",
    operation_version="1",
)
def near_vertex(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "vertex")


@operation(
    backend=ops.near_edge,
    result=EDGE_SPEC,
    returns=Edge,
    operation_id="zencad.typed.shape.near_edge",
    operation_version="1",
)
def near_edge(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "edge")


@operation(
    backend=ops.near_wire,
    result=WIRE_SPEC,
    returns=Wire,
    operation_id="zencad.typed.shape.near_wire",
    operation_version="1",
)
def near_wire(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "wire")


@operation(
    backend=ops.near_face,
    result=FACE_SPEC,
    returns=Face,
    operation_id="zencad.typed.shape.near_face",
    operation_version="1",
)
def near_face(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "face")


@operation(
    backend=ops.near_shell,
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.shape.near_shell",
    operation_version="1",
)
def near_shell(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "shell")


@operation(
    backend=ops.near_solid,
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.shape.near_solid",
    operation_version="1",
)
def near_solid(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "solid")


@operation(
    backend=ops.near_compsolid,
    result=COMPSOLID_SPEC,
    returns=CompSolid,
    operation_id="zencad.typed.shape.near_compsolid",
    operation_version="1",
)
def near_compsolid(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "compsolid")


@operation(
    backend=ops.near_compound,
    result=COMPOUND_SPEC,
    returns=Compound,
    operation_id="zencad.typed.shape.near_compound",
    operation_version="1",
)
def near_compound(shape: Shape, point: Point3, /) -> OperationArguments:
    return _near_arguments(shape, point, "compound")


def project_point_on_curve(
    point: Point3,
    target: Curve | Edge,
    /,
) -> CurveProjection:
    if not isinstance(point, Point3):
        raise TypeError("project_point_on_curve point must be Point3")
    if not isinstance(target, (Curve, Edge)):
        raise TypeError("project_point_on_curve target must be Curve or Edge")
    resolve_runtime(point, target)
    curve = target.curve() if isinstance(target, Edge) else target
    parameter = curve.lower_distance_parameter(point)
    projected = curve.point(parameter)
    return CurveProjection(projected, parameter, (projected - point).length())


def project(point: Point3, target: Curve | Edge, /) -> CurveProjection:
    return project_point_on_curve(point, target)


@operation(
    backend=bound_ops.shape_boundary_box,
    result=BOUNDARY_BOX_SPEC,
    returns=BoundaryBox,
    operation_id="zencad.typed.shape.boundbox",
    operation_version="1",
)
def boundbox(shape: Shape, /) -> OperationArguments:
    _require_shape(shape, "boundbox")
    return arguments(shape)


def _near_arguments(shape: Shape, point: Point3, name: str) -> OperationArguments:
    _require_shape(shape, f"near_{name}")
    if not isinstance(point, Point3):
        raise TypeError(f"near_{name} expects Point3")
    resolve_runtime(shape, point)
    return arguments(shape, point)


def _require_references(
    references: Sequence[Point3] | None,
    name: str,
) -> tuple[Point3, ...] | None:
    if references is None:
        return None
    if isinstance(references, (str, bytes)) or not isinstance(references, Sequence):
        raise TypeError(f"{name} references must be Point3 values")
    values = tuple(references)
    if not all(isinstance(value, Point3) for value in values):
        raise TypeError(f"{name} references must be Point3 values")
    resolve_runtime(values)
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
    resolve_runtime(values)
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
    resolve_runtime(values)
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
    resolve_runtime(values)
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
    "boundbox",
    "chamfer",
    "chamfer2d",
    "draft",
    "fillet",
    "fillet2d",
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
]
