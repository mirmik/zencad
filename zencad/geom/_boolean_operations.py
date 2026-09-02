"""Resolved topology-zero and boolean operations for typed Shape handles."""

from __future__ import annotations

from OCP.BRep import BRep_Builder
from OCP.BOPAlgo import BOPAlgo_BOP, BOPAlgo_FUSE, BOPAlgo_Splitter
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Section,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.GeomAbs import GeomAbs_Plane
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

from zencad._native.shape import Shape as ResolvedShape


_BOOLEAN_FUZZY_TOLERANCE = 1e-7


def _has_solid(shape: ResolvedShape) -> bool:
    return TopExp_Explorer(shape.Shape(), TopAbs_SOLID).More()


def _fuse(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    algorithm = BRepAlgoAPI_Fuse(left.Shape(), right.Shape())
    algorithm.SetNonDestructive(True)
    algorithm.SetFuzzyValue(_BOOLEAN_FUZZY_TOLERANCE)
    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError("boolean union failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


def _bop_fuse(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    algorithm = BOPAlgo_BOP()
    algorithm.AddArgument(left.Shape())
    algorithm.AddTool(right.Shape())
    algorithm.SetOperation(BOPAlgo_FUSE)
    algorithm.SetNonDestructive(True)
    algorithm.SetFuzzyValue(_BOOLEAN_FUZZY_TOLERANCE)
    algorithm.Perform()
    if algorithm.HasErrors():
        raise ValueError("boolean union fallback failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


def empty_shape() -> ResolvedShape:
    """Return the algebraic zero of topology as a serializable empty Shape."""

    compound = TopoDS_Compound()
    BRep_Builder().MakeCompound(compound)
    return ResolvedShape(compound)


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    algorithm = BRepAlgoAPI_Cut(left.Shape(), right.Shape())
    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError("boolean difference failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


def union(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    solid_operands = _has_solid(left) and _has_solid(right)
    result = _fuse(left, right)
    if solid_operands and not _has_solid(result):
        # OCCT's pave-filler can be operand-order sensitive for coincident
        # boundaries on some platforms even though union is commutative.
        result = _fuse(right, left)
    if solid_operands and not _has_solid(result):
        result = _bop_fuse(left, right)
    if solid_operands and not _has_solid(result):
        raise ValueError("boolean union produced an empty solid result")
    return result


def intersection(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    algorithm = BRepAlgoAPI_Common(left.Shape(), right.Shape())
    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError("boolean intersection failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


def union_shapes(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    """Fuse a sequence with the balanced reduction used by the legacy API."""

    work = list(shapes)
    while len(work) > 1:
        pair_count = len(work) // 2
        reduced = [union(work[index], work[-index - 1]) for index in range(pair_count)]
        if len(work) % 2:
            reduced.append(work[pair_count])
        work = reduced
    return work[0]


def difference_shapes(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    result = shapes[0]
    for index, shape in enumerate(shapes[1:], start=2):
        try:
            result = difference(result, shape)
        except ValueError as error:
            raise ValueError(
                f"boolean difference failed at operand {index} of {len(shapes)}"
            ) from error
    return result


def intersection_shapes(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    result = shapes[0]
    for index, shape in enumerate(shapes[1:], start=2):
        try:
            result = intersection(result, shape)
        except ValueError as error:
            raise ValueError(
                f"boolean intersection failed at operand {index} of {len(shapes)}"
            ) from error
    return result


def section(
    left: ResolvedShape,
    right: ResolvedShape,
    pretty: bool,
) -> ResolvedShape:
    algorithm = BRepAlgoAPI_Section(left.Shape(), right.Shape())
    if pretty:
        algorithm.ComputePCurveOn1(True)
        algorithm.Approximation(True)
    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError("section failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


def _solid_sort_key(shape: ResolvedShape) -> tuple[float, ...]:
    center = shape.center()
    bounds = shape.boundbox()
    return tuple(
        round(value, 12)
        for value in (
            center.x,
            center.y,
            center.z,
            bounds.xmin,
            bounds.ymin,
            bounds.zmin,
            bounds.xmax,
            bounds.ymax,
            bounds.zmax,
            shape.mass(),
        )
    )


def _solid_parts(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    explorer = TopExp_Explorer(shape.Shape(), TopAbs_SOLID)
    parts = []
    while explorer.More():
        parts.append(ResolvedShape(TopoDS.Solid_s(explorer.Current())))
        explorer.Next()
    return tuple(sorted(parts, key=_solid_sort_key))


def _split_resolved(
    body: ResolvedShape,
    tools: tuple[ResolvedShape, ...],
) -> tuple[ResolvedShape, ...]:
    if not isinstance(body, ResolvedShape):
        raise TypeError("split body must be a Shape")
    if not tools:
        raise ValueError("split requires at least one tool Shape")
    if not all(isinstance(tool, ResolvedShape) for tool in tools):
        raise TypeError("split tools must contain only Shape values")

    original_count = len(_solid_parts(body))
    if original_count == 0:
        raise TypeError("split body must contain at least one solid")

    algorithm = BOPAlgo_Splitter()
    algorithm.SetNonDestructive(True)
    algorithm.AddArgument(body.Shape())
    for tool in tools:
        algorithm.AddTool(tool.Shape())
    algorithm.Perform()
    if algorithm.HasErrors():
        raise ValueError("OCCT splitter failed for the supplied body and tools")

    parts = _solid_parts(ResolvedShape(algorithm.Shape()))
    if len(parts) <= original_count:
        raise ValueError("split tools do not divide the body")
    return parts


def _coordinates(value: object, name: str) -> tuple[float, float, float]:
    try:
        coordinates = (float(value.x), float(value.y), float(value.z))
    except AttributeError:
        try:
            coordinates = tuple(float(item) for item in value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{name} must contain three numeric coordinates") from error
    if len(coordinates) != 3:
        raise TypeError(f"{name} must contain three numeric coordinates")
    return coordinates


def _coordinate_plane(coordinate: float, axis: object) -> gp_Pln:
    if isinstance(axis, str):
        normals = {
            "x": (1.0, 0.0, 0.0),
            "y": (0.0, 1.0, 0.0),
            "z": (0.0, 0.0, 1.0),
        }
        try:
            normal = normals[axis.lower()]
        except KeyError as error:
            raise ValueError("slice axis must be 'x', 'y', 'z', or a vector") from error
    else:
        normal = _coordinates(axis, "slice axis")
    try:
        direction = gp_Dir(*normal)
    except Exception as error:
        raise ValueError("slice plane normal must be non-zero") from error
    distance = float(coordinate)
    return gp_Pln(
        gp_Pnt(
            direction.X() * distance,
            direction.Y() * distance,
            direction.Z() * distance,
        ),
        direction,
    )


def _resolved_plane(
    plane: object,
    coordinate: float,
    axis: object,
) -> gp_Pln:
    if plane is None:
        return _coordinate_plane(coordinate, axis)
    if isinstance(plane, ResolvedShape):
        if not plane.is_face():
            raise TypeError("slice plane Shape must be a planar face")
        adaptor = BRepAdaptor_Surface(plane.Face())
        if adaptor.GetType() != GeomAbs_Plane:
            raise TypeError("slice plane Shape must be a planar face")
        return adaptor.Plane()
    try:
        origin, normal = plane
    except (TypeError, ValueError) as error:
        raise TypeError(
            "slice plane must be a planar face or (origin, normal)"
        ) from error
    try:
        return gp_Pln(
            gp_Pnt(*_coordinates(origin, "slice plane origin")),
            gp_Dir(*_coordinates(normal, "slice plane normal")),
        )
    except Exception as error:
        raise ValueError("slice plane normal must be non-zero") from error


def _slice_resolved(
    body: ResolvedShape,
    plane: object,
    coordinate: float,
    axis: object,
) -> tuple[ResolvedShape, ...]:
    resolved_plane = _resolved_plane(plane, coordinate, axis)
    tool = ResolvedShape(BRepBuilderAPI_MakeFace(resolved_plane).Face())
    parts = _split_resolved(body, (tool,))
    if len(parts) != 2:
        raise ValueError(
            f"slice requires exactly two resulting solids; got {len(parts)}"
        )

    location = resolved_plane.Location()
    direction = resolved_plane.Axis().Direction()

    def signed_center(shape: ResolvedShape) -> float:
        center = shape.center()
        return (
            (center.x - location.X()) * direction.X()
            + (center.y - location.Y()) * direction.Y()
            + (center.z - location.Z()) * direction.Z()
        )

    return tuple(sorted(parts, key=signed_center))


def split_shapes(
    body: ResolvedShape,
    tools: tuple[ResolvedShape, ...],
) -> tuple[ResolvedShape, ...]:
    return _split_resolved(body, tools)


def slice_shape(
    body: ResolvedShape,
    plane: object,
    coordinate: float,
    axis: object,
) -> tuple[ResolvedShape, ...]:
    return _slice_resolved(body, plane, coordinate, axis)
