"""Resolved topology-zero and boolean operations for typed Shape handles."""

from __future__ import annotations

from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Section,
)
from OCP.TopoDS import TopoDS_Compound

from zencad.geom.shape import Shape as ResolvedShape


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
    algorithm = BRepAlgoAPI_Fuse(left.Shape(), right.Shape())
    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError("boolean union failed for Shape operands")
    return ResolvedShape(algorithm.Shape())


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
