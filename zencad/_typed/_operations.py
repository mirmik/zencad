"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

import math
from typing import Callable

from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Transform,
)
from OCP.BRepTools import BRepTools
from OCP.GC import GC_MakeArcOfCircle
from OCP.Geom import Geom_RectangularTrimmedSurface, Geom_TrimmedCurve
from OCP.gp import gp_Pnt
from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHELL,
    TopAbs_SOLID,
    TopAbs_WIRE,
    TopAbs_ShapeEnum,
    TopAbs_VERTEX,
)
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shape, TopoDS_Wire

from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.solid import (
    _box,
    _cone,
    _cylinder,
    _halfspace,
    _make_solid,
    _sphere,
    _torus,
)
from zencad.geom.trans import move
from zencad.occ_compat import (
    as_compound,
    as_compsolid,
    as_edge,
    as_face,
    as_shell,
    as_solid,
    as_vertex,
    as_wire,
    vertex_point as ocp_vertex_point,
)
from zencad.runtime.scene_protocol import decode_brep, encode_brep

from ._transform_operations import TransformValue, transform_to_ocp
from ._curve_operations import CurveValue, curve_from_ocp, curve_to_ocp
from ._surface_operations import SurfaceValue, surface_from_ocp
from ._value_operations import Point3Value, Vector3Value


def _point(value: Point3Value) -> gp_Pnt:
    return gp_Pnt(value.x, value.y, value.z)


def box(
    size: Vector3Value,
    center: bool | str | None,
) -> ResolvedShape:
    return _box(size.x, size.y, size.z, center=center)


def sphere(
    radius: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    return _sphere(radius, yaw=yaw, pitch=pitch)


def cylinder(
    radius: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    return _cylinder(radius, height, yaw=yaw, center=center)


def cone(
    radius1: float,
    radius2: float,
    height: float,
    yaw: float | None,
    center: bool,
) -> ResolvedShape:
    return _cone(radius1, radius2, height, yaw=yaw, center=center)


def torus(
    radius1: float,
    radius2: float,
    yaw: float | None,
    pitch: float | tuple[float, float] | None,
) -> ResolvedShape:
    return _torus(radius1, radius2, yaw=yaw, pitch=pitch)


def halfspace() -> ResolvedShape:
    return _halfspace()


def make_solid(shells: tuple[ResolvedShape, ...]) -> ResolvedShape:
    return _make_solid(shells)


def empty_shape() -> ResolvedShape:
    """Return the algebraic zero of topology as a serializable empty Shape."""
    compound = TopoDS_Compound()
    BRep_Builder().MakeCompound(compound)
    return ResolvedShape(compound)


def segment(start: Point3Value, end: Point3Value) -> ResolvedShape:
    return ResolvedShape(BRepBuilderAPI_MakeEdge(_point(start), _point(end)).Edge())


def _polygon_wire(
    points: tuple[Point3Value, ...],
    *,
    closed: bool,
) -> TopoDS_Wire:
    if len(points) < 2:
        raise ValueError("polysegment requires at least two points")
    builder = BRepBuilderAPI_MakePolygon()
    for point in points:
        builder.Add(_point(point))
    if closed:
        builder.Close()
    if not builder.IsDone():
        raise ValueError("cannot build a wire from the supplied points")
    return builder.Wire()


def polysegment(
    points: tuple[Point3Value, ...],
    closed: bool,
) -> ResolvedShape:
    return ResolvedShape(_polygon_wire(points, closed=closed))


def polygon(points: tuple[Point3Value, ...]) -> ResolvedShape:
    if len(points) < 3:
        raise ValueError("polygon requires at least three points")
    wire = _polygon_wire(points, closed=True)
    builder = BRepBuilderAPI_MakeFace(wire)
    if not builder.IsDone():
        raise ValueError("cannot build a face from the supplied points")
    return ResolvedShape(builder.Face())


def rectangle(width: float, height: float, center: bool) -> ResolvedShape:
    x0 = -width / 2 if center else 0.0
    y0 = -height / 2 if center else 0.0
    points = (
        Point3Value(x0, y0, 0.0),
        Point3Value(x0 + width, y0, 0.0),
        Point3Value(x0 + width, y0 + height, 0.0),
        Point3Value(x0, y0 + height, 0.0),
    )
    return polygon(points)


def translate(shape: ResolvedShape, vector: Vector3Value) -> ResolvedShape:
    return shape.transform(move(vector.x, vector.y, vector.z))


def transform(shape: ResolvedShape, value: TransformValue) -> ResolvedShape:
    transformed = BRepBuilderAPI_Transform(
        shape.Shape(), transform_to_ocp(value), True
    ).Shape()
    return ResolvedShape(transformed)


def difference(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left - right


def union(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left + right


def intersection(left: ResolvedShape, right: ResolvedShape) -> ResolvedShape:
    return left ^ right


def shape_from_brep(payload: bytes) -> ResolvedShape:
    """Restore an immutable BREP snapshot inside the evaluation graph."""
    if not isinstance(payload, bytes):
        raise TypeError("shape_from_brep expects bytes")
    return ResolvedShape(decode_brep(payload))


def shape_to_ocp(value: ResolvedShape) -> TopoDS_Shape:
    """Return an independent OCP snapshot, never the stored mutable wrapper."""
    if not isinstance(value, ResolvedShape):
        raise TypeError("shape_to_ocp expects a resolved ZenCad Shape")
    native = value.Shape()
    if native.IsNull():
        raise ValueError("typed topology handles cannot contain a null shape")
    return decode_brep(encode_brep(native))


def _subshapes(
    shape: ResolvedShape,
    kind: TopAbs_ShapeEnum,
    convert: Callable[[TopoDS_Shape], TopoDS_Shape],
) -> tuple[ResolvedShape, ...]:
    """Preserve the legacy TopExp_Explorer occurrence semantics."""
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("cannot enumerate a null shape")
    explorer = TopExp_Explorer(native, kind)
    values: list[ResolvedShape] = []
    while explorer.More():
        values.append(ResolvedShape(convert(explorer.Current())))
        explorer.Next()
    return tuple(values)


def vertices(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    """Return vertices unique by OCCT IsSame topology identity."""
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("cannot enumerate a null shape")
    values = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(native, TopAbs_VERTEX, values)
    return tuple(
        ResolvedShape(as_vertex(values.FindKey(index)))
        for index in range(1, values.Extent() + 1)
    )


def edges(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_EDGE, as_edge)


def wires(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_WIRE, as_wire)


def faces(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_FACE, as_face)


def shells(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_SHELL, as_shell)


def solids(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_SOLID, as_solid)


def compounds(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_COMPOUND, as_compound)


def compsolids(shape: ResolvedShape) -> tuple[ResolvedShape, ...]:
    return _subshapes(shape, TopAbs_COMPSOLID, as_compsolid)


_SHAPE_KIND_NAMES = {
    int(TopAbs_VERTEX): "vertex",
    int(TopAbs_EDGE): "edge",
    int(TopAbs_WIRE): "wire",
    int(TopAbs_FACE): "face",
    int(TopAbs_SHELL): "shell",
    int(TopAbs_SOLID): "solid",
    int(TopAbs_COMPSOLID): "compsolid",
    int(TopAbs_COMPOUND): "compound",
}


def shape_kind(shape: ResolvedShape) -> str:
    native = shape.Shape()
    if native.IsNull():
        raise ValueError("typed Shape cannot be null")
    try:
        return _SHAPE_KIND_NAMES[int(native.ShapeType())]
    except KeyError as exception:
        raise ValueError("unsupported topology kind") from exception


def shape_has_kind(shape: ResolvedShape, kind: int) -> bool:
    return int(shape.Shape().ShapeType()) == kind


def shape_is_wire_or_edge(shape: ResolvedShape) -> bool:
    return int(shape.Shape().ShapeType()) in (int(TopAbs_WIRE), int(TopAbs_EDGE))


def shape_is_closed(shape: ResolvedShape) -> bool:
    if not shape_is_wire_or_edge(shape):
        raise TypeError("is_closed is only defined for Edge or Wire")
    return bool(shape.is_closed())


def shape_is_volumed(shape: ResolvedShape) -> bool:
    explorer = TopExp_Explorer(shape.Shape(), TopAbs_SOLID)
    return explorer.More()


def wire_from_wire_or_edge(shape: ResolvedShape) -> ResolvedShape:
    native = shape.Shape()
    if native.ShapeType() == TopAbs_WIRE:
        return ResolvedShape(as_wire(native))
    if native.ShapeType() == TopAbs_EDGE:
        return ResolvedShape(BRepBuilderAPI_MakeWire(as_edge(native)).Wire())
    raise TypeError("Wire_orEdgeToWire expects Edge or Wire")


def shape_endpoint(shape: ResolvedShape, finish: bool) -> Point3Value:
    start, end = shape.endpoints()
    point = end if finish else start
    return Point3Value(float(point.x), float(point.y), float(point.z))


def curve_trimmed_edge(
    curve: CurveValue,
    start: float,
    end: float,
) -> ResolvedShape:
    edge = BRepBuilderAPI_MakeEdge(curve_to_ocp(curve), start, end).Edge()
    if edge.IsNull():
        raise ValueError("trimmed edge construction failed")
    return ResolvedShape(edge)


def curve_edge(
    curve: CurveValue,
    interval: tuple[float, float] | None,
) -> ResolvedShape:
    native_curve = curve_to_ocp(curve)
    builder = (
        BRepBuilderAPI_MakeEdge(native_curve)
        if interval is None
        else BRepBuilderAPI_MakeEdge(native_curve, interval[0], interval[1])
    )
    if not builder.IsDone():
        raise ValueError("edge construction from Curve failed")
    return ResolvedShape(builder.Edge())


def circle_arc(
    start: Point3Value,
    middle: Point3Value,
    end: Point3Value,
) -> ResolvedShape:
    arc = GC_MakeArcOfCircle(_point(start), _point(middle), _point(end))
    if not arc.IsDone():
        raise ValueError("circle arc construction failed")
    builder = BRepBuilderAPI_MakeEdge(arc.Value())
    if not builder.IsDone():
        raise ValueError("circle arc edge construction failed")
    return ResolvedShape(builder.Edge())


def make_wire(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    if not shapes:
        raise ValueError("make_wire requires at least one Edge or Wire")
    builder = BRepBuilderAPI_MakeWire()
    for shape in shapes:
        native = shape.Shape()
        if native.ShapeType() == TopAbs_EDGE:
            builder.Add(as_edge(native))
        elif native.ShapeType() == TopAbs_WIRE:
            builder.Add(as_wire(native))
        else:
            raise TypeError("make_wire accepts only Edge or Wire")
    if not builder.IsDone():
        raise ValueError("wire construction failed")
    return ResolvedShape(builder.Wire())


def helix(
    radius: float,
    height: float,
    step: float | None,
    pitch: float | None,
    angle: float,
    left: bool,
) -> ResolvedShape:
    from zencad.geom.wire import _helix

    return _helix(radius, height, step=step, pitch=pitch, angle=angle, left=left)


def rounded_polysegment(
    points: tuple[Point3Value, ...],
    radius: float,
    closed: bool,
) -> ResolvedShape:
    from . import _curve_operations as curve_ops

    if len(points) < 2:
        raise ValueError("rounded_polysegment requires at least two points")
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("rounded_polysegment radius must be finite and positive")

    def subtract(left: Point3Value, right: Point3Value) -> Vector3Value:
        return Vector3Value(left.x - right.x, left.y - right.y, left.z - right.z)

    def add(point: Point3Value, vector: Vector3Value) -> Point3Value:
        return Point3Value(
            point.x + vector.x,
            point.y + vector.y,
            point.z + vector.z,
        )

    def scale(vector: Vector3Value, factor: float) -> Vector3Value:
        return Vector3Value(vector.x * factor, vector.y * factor, vector.z * factor)

    def dot(left: Vector3Value, right: Vector3Value) -> float:
        return left.x * right.x + left.y * right.y + left.z * right.z

    def cross(left: Vector3Value, right: Vector3Value) -> Vector3Value:
        return Vector3Value(
            left.y * right.z - left.z * right.y,
            left.z * right.x - left.x * right.z,
            left.x * right.y - left.y * right.x,
        )

    def length(vector: Vector3Value) -> float:
        return math.sqrt(dot(vector, vector))

    def project(
        point: Point3Value,
        line_start: Point3Value,
        line_end: Point3Value,
    ) -> Point3Value:
        direction = subtract(line_end, line_start)
        denominator = dot(direction, direction)
        if denominator == 0:
            raise ValueError("rounded_polysegment contains duplicate points")
        parameter = dot(subtract(point, line_start), direction) / denominator
        return add(line_start, scale(direction, parameter))

    source = list(points)
    if closed:
        if len(source) < 3:
            raise ValueError(
                "closed rounded_polysegment requires at least three points"
            )
        source.insert(0, source[-1])
        source.append(source[1])

    corners = source[1:-1]
    pairs: list[tuple[Point3Value | None, Point3Value | None]] = [(None, source[0])]
    tangent_pairs: list[tuple[Vector3Value, Vector3Value] | None] = []

    for index, corner in enumerate(corners):
        first_direction = subtract(source[index + 1], source[index])
        second_direction = subtract(source[index + 2], source[index + 1])
        normal = cross(second_direction, first_direction)
        if length(normal) <= 1e-12:
            pairs.append((corner, corner))
            tangent_pairs.append(None)
            continue
        first_normal = cross(first_direction, normal)
        second_normal = cross(second_direction, normal)
        bisector = Vector3Value(
            first_normal.x + second_normal.x,
            first_normal.y + second_normal.y,
            first_normal.z + second_normal.z,
        )
        bisector_length = length(bisector)
        if bisector_length <= 1e-12:
            pairs.append((corner, corner))
            tangent_pairs.append(None)
            continue
        center = add(corner, scale(bisector, radius / bisector_length))
        first_projection = project(center, source[index], source[index + 1])
        second_projection = project(center, source[index + 1], source[index + 2])
        pairs.append((first_projection, second_projection))
        tangent_pairs.append((first_direction, second_direction))

    pairs.append((source[-1], None))
    nodes: list[ResolvedShape] = []
    for index, tangents in enumerate(tangent_pairs):
        line_start = pairs[index][1]
        line_end = pairs[index + 1][0]
        arc_start = pairs[index + 1][0]
        arc_end = pairs[index + 1][1]
        assert line_start is not None and line_end is not None
        nodes.append(segment(line_start, line_end))
        if tangents is not None:
            assert arc_start is not None and arc_end is not None
            curve = curve_ops.interpolate(
                (arc_start, arc_end),
                tangents,
                False,
            )
            nodes.append(curve_edge(curve, None))

    final_start = pairs[-2][1]
    final_end = pairs[-1][0]
    assert final_start is not None and final_end is not None
    nodes.append(segment(final_start, final_end))

    if closed:
        nodes = nodes[1:-1]
    result = make_wire(tuple(nodes))
    if closed:
        start, end = result.endpoints()
        closing = segment(
            Point3Value(start.x, start.y, start.z),
            Point3Value(end.x, end.y, end.z),
        )
        result = make_wire((result, closing))
    return result


def _legacy_points(values: tuple[Point3Value, ...] | None):
    if values is None:
        return None
    return [(value.x, value.y, value.z) for value in values]


def fill_shape(shape: ResolvedShape) -> ResolvedShape:
    from zencad.geom.face import _fill

    return _fill(shape)


def extrude_shape(
    shape: ResolvedShape,
    vector: Vector3Value,
    center: bool,
) -> ResolvedShape:
    from zencad.geom.sweep import _extrude

    return _extrude(shape, (vector.x, vector.y, vector.z), center=center)


def fillet_shape(
    shape: ResolvedShape,
    radius: float,
    references: tuple[Point3Value, ...] | None,
) -> ResolvedShape:
    from zencad.geom.operations import _fillet

    return _fillet(shape, radius, refs=_legacy_points(references))


def chamfer_shape(
    shape: ResolvedShape,
    radius: float,
    references: tuple[Point3Value, ...] | None,
) -> ResolvedShape:
    from zencad.geom.operations import _chamfer

    return _chamfer(shape, radius, refs=_legacy_points(references))


def fillet2d_shape(
    shape: ResolvedShape,
    radius: float,
    references: tuple[Point3Value, ...] | None,
) -> ResolvedShape:
    from zencad.geom.operations import _fillet2d

    return _fillet2d(shape, radius, refs=_legacy_points(references))


def chamfer2d_shape(
    shape: ResolvedShape,
    radius: float,
    references: tuple[Point3Value, ...] | None,
) -> ResolvedShape:
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet2d
    from OCP.TopExp import TopExp_Explorer

    from zencad.geom.near import _near_vertex

    if radius <= 0:
        raise ValueError("chamfer2d radius must be positive")
    if not shape.is_face():
        raise TypeError("chamfer2d expects Face")
    builder = BRepFilletAPI_MakeFillet2d(shape.Face())
    resolved_references = _legacy_points(references)
    if resolved_references is None:
        resolved_references = shape.vertices()
    for reference in resolved_references:
        vertex = _near_vertex(shape, reference).Vertex()
        edges = TopExp_Explorer(shape.Shape(), TopAbs_EDGE)
        selected_edge = None
        while edges.More() and selected_edge is None:
            edge = as_edge(edges.Current())
            edge_vertices = TopExp_Explorer(edge, TopAbs_VERTEX)
            while edge_vertices.More():
                if as_vertex(edge_vertices.Current()).IsSame(vertex):
                    selected_edge = edge
                    break
                edge_vertices.Next()
            edges.Next()
        if selected_edge is None:
            raise ValueError("cannot find an edge adjacent to chamfer vertex")
        builder.AddChamfer(selected_edge, vertex, radius, math.pi / 4)
    result = builder.Shape()
    if result.IsNull():
        raise ValueError("chamfer2d construction failed")
    return ResolvedShape(result)


def sequence_item(sequence: tuple[ResolvedShape, ...], index: int) -> ResolvedShape:
    return sequence[index]


def mass(shape: ResolvedShape) -> float:
    return float(shape.mass())


def center(shape: ResolvedShape) -> Point3Value:
    value = shape.center()
    return Point3Value(float(value.x), float(value.y), float(value.z))


def surface_mass(shape: ResolvedShape) -> float:
    return float(shape.SurfaceProperties().Mass())


def surface_center(shape: ResolvedShape) -> Point3Value:
    point = shape.SurfaceProperties().CentreOfMass()
    return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))


def volume_mass(shape: ResolvedShape) -> float:
    return float(shape.VolumeProperties().Mass())


def volume_center(shape: ResolvedShape) -> Point3Value:
    point = shape.VolumeProperties().CentreOfMass()
    return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))


def vertex_point(shape: ResolvedShape) -> Point3Value:
    native = shape.Shape()
    if native.IsNull() or not shape.is_vertex():
        raise TypeError("vertex_point expects a non-null Vertex")
    value = ocp_vertex_point(shape.Vertex())
    return Point3Value(float(value.X()), float(value.Y()), float(value.Z()))


def edge_curve(shape: ResolvedShape) -> CurveValue:
    """Snapshot an edge's geometry with its finite topological range."""
    native = shape.Shape()
    if native.IsNull() or not shape.is_edge():
        raise TypeError("edge_curve expects a non-null Edge")
    edge = shape.Edge()
    curve = BRep_Tool.Curve_s(edge, 0.0, 0.0)
    first, last = BRep_Tool.Range_s(edge)
    return curve_from_ocp(Geom_TrimmedCurve(curve, first, last))


def face_surface(shape: ResolvedShape) -> SurfaceValue:
    """Snapshot a face's basis surface over its finite UV bounds."""
    native = shape.Shape()
    if native.IsNull() or not shape.is_face():
        raise TypeError("face_surface expects a non-null Face")
    face = shape.Face()
    surface = BRep_Tool.Surface_s(face)
    u_first, u_last, v_first, v_last = BRepTools.UVBounds_s(face)
    return surface_from_ocp(
        Geom_RectangularTrimmedSurface(
            surface,
            u_first,
            u_last,
            v_first,
            v_last,
        )
    )
