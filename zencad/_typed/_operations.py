"""Resolved operations used by the experimental typed domain layer.

The functions in this module are the narrow adapter between domain handles and
the current eager ZenCad/OCP implementation.  They deliberately accept and
return resolved values only; expression construction lives in ``runtime``.
"""

from __future__ import annotations

import math
from typing import Callable

from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Section,
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_GTransform,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Transform,
)
from OCP.BRepOffsetAPI import (
    BRepOffsetAPI_MakeOffsetShape,
    BRepOffsetAPI_MakeThickSolid,
)
from OCP.BRepTools import BRepTools
from OCP.GC import GC_MakeArcOfCircle
from OCP.Geom import (
    Geom_Circle,
    Geom_Ellipse,
    Geom_RectangularTrimmedSurface,
    Geom_TrimmedCurve,
)
from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCP.GeomAbs import GeomAbs_C2
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Shell, ShapeFix_Solid
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.gp import gp_Ax2, gp_Dir, gp_Pln, gp_Pnt
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
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_ListOfShape
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shape, TopoDS_Shell, TopoDS_Wire

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
    build_curves_3d,
    make_fill_face,
    make_sewing,
    vertex_point as ocp_vertex_point,
)
from zencad.runtime.scene_protocol import decode_brep, encode_brep

from ._transform_operations import (
    AffineTransformValue,
    TransformValue,
    affine_to_ocp,
    transform_to_ocp,
)
from ._curve_operations import (
    Curve2Value,
    CurveValue,
    curve2_to_ocp,
    curve_from_ocp,
    curve_to_ocp,
)
from ._surface_operations import (
    SurfaceValue,
    surface_from_ocp,
    surface_to_ocp,
)
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


def _single_face_shell(face: ResolvedShape) -> ResolvedShape:
    shell = TopoDS_Shell()
    builder = BRep_Builder()
    builder.MakeShell(shell)
    builder.Add(shell, as_face(face.Shape()))
    return ResolvedShape(shell)


def make_shell(faces: tuple[ResolvedShape, ...]) -> ResolvedShape:
    if not faces:
        raise ValueError("make_shell requires at least one Face")
    if len(faces) == 1:
        return _single_face_shell(faces[0])

    sewing = make_sewing()
    for face in faces:
        sewing.Add(as_face(face.Shape()))
    sewing.Perform()
    sewed = sewing.SewedShape()
    if sewed.IsNull():
        raise ValueError("cannot sew the supplied faces into a Shell")
    if sewed.ShapeType() == TopAbs_FACE:
        return _single_face_shell(ResolvedShape(as_face(sewed)))
    if sewed.ShapeType() != TopAbs_SHELL:
        raise ValueError("supplied faces do not form one Shell")
    fixer = ShapeFix_Shell(as_shell(sewed))
    fixer.Perform()
    return ResolvedShape(fixer.Shell())


def fill_shell(shell: ResolvedShape) -> ResolvedShape:
    fixer = ShapeFix_Solid()
    solid = fixer.SolidFromShell(as_shell(shell.Shape()))
    fixer.Init(solid)
    fixer.Perform()
    return ResolvedShape(fixer.Solid())


def polyhedron_shell(
    points: tuple[Point3Value, ...],
    faces: tuple[tuple[int, ...], ...],
) -> ResolvedShape:
    built_faces = tuple(
        polygon(tuple(points[index] for index in face)) for face in faces
    )
    return make_shell(built_faces)


def convex_hull_faces(
    points: tuple[Point3Value, ...],
    incremental: bool,
    qhull_options: str | None,
) -> tuple[tuple[int, ...], ...]:
    from scipy.spatial import ConvexHull

    hull = ConvexHull(
        tuple((point.x, point.y, point.z) for point in points),
        incremental=incremental,
        qhull_options=qhull_options,
    )
    return tuple(tuple(int(index) for index in face) for face in hull.simplices)


def convex_hull_shape(
    points: tuple[Point3Value, ...],
    incremental: bool,
    qhull_options: str | None,
    shell: bool,
) -> ResolvedShape:
    faces = convex_hull_faces(points, incremental, qhull_options)
    hull_shell = polyhedron_shell(points, faces)
    if shell:
        return hull_shell
    return fill_shell(hull_shell)


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


def fill_wires(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    if not shapes:
        raise ValueError("fill requires at least one Edge or Wire")
    wires = tuple(as_wire(wire_from_wire_or_edge(shape).Shape()) for shape in shapes)
    builder = BRepBuilderAPI_MakeFace(wires[0])
    for wire in wires[1:]:
        builder.Add(wire)
    builder.Build()
    if not builder.IsDone():
        raise ValueError("cannot fill the supplied wires")
    fixer = ShapeFix_Face(builder.Face())
    fixer.Perform()
    fixer.FixOrientation()
    return ResolvedShape(fixer.Face())


def _angle_pair(
    angle: float | tuple[float, float] | None,
) -> tuple[float, float] | None:
    if angle is None:
        return None
    if isinstance(angle, tuple):
        start, end = angle
    elif angle >= 0:
        start, end = 0.0, angle
    else:
        start, end = angle, 0.0
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError("conic angle bounds must be finite")
    if start == end:
        raise ValueError("conic angle bounds must be distinct")
    return (start, end)


def _conic_shape(
    curve: Geom_Circle | Geom_Ellipse,
    angle: float | tuple[float, float] | None,
    wire: bool,
) -> ResolvedShape:
    interval = _angle_pair(angle)
    if interval is None:
        edge_builder = BRepBuilderAPI_MakeEdge(curve)
    else:
        lower, upper = sorted(interval)
        edge_builder = BRepBuilderAPI_MakeEdge(curve, lower, upper)
    if not edge_builder.IsDone():
        raise ValueError("conic edge construction failed")
    edge = edge_builder.Edge()
    if interval is not None and interval[1] < interval[0]:
        edge = as_edge(edge.Reversed())
    if wire:
        return ResolvedShape(edge)

    wire_builder = BRepBuilderAPI_MakeWire()
    wire_builder.Add(edge)
    if interval is not None:
        start = curve.Value(interval[0])
        end = curve.Value(interval[1])
        origin = curve.Location()
        wire_builder.Add(BRepBuilderAPI_MakeEdge(end, origin).Edge())
        wire_builder.Add(BRepBuilderAPI_MakeEdge(origin, start).Edge())
    if not wire_builder.IsDone():
        raise ValueError("conic boundary construction failed")
    face_builder = BRepBuilderAPI_MakeFace(wire_builder.Wire())
    if not face_builder.IsDone():
        raise ValueError("conic face construction failed")
    return ResolvedShape(face_builder.Face())


def circle_shape(
    radius: float,
    angle: float | tuple[float, float] | None,
    wire: bool,
) -> ResolvedShape:
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("circle radius must be finite and positive")
    curve = Geom_Circle(
        gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        radius,
    )
    return _conic_shape(curve, angle, wire)


def ellipse_shape(
    radius1: float,
    radius2: float,
    angle: float | tuple[float, float] | None,
    wire: bool,
) -> ResolvedShape:
    if not math.isfinite(radius1) or radius1 <= 0:
        raise ValueError("ellipse radius1 must be finite and positive")
    if not math.isfinite(radius2) or radius2 <= 0:
        raise ValueError("ellipse radius2 must be finite and positive")
    axis_angle = 0.0
    if radius2 > radius1:
        radius1, radius2 = radius2, radius1
        axis_angle = math.pi / 2
    curve = Geom_Ellipse(
        gp_Ax2(
            gp_Pnt(0, 0, 0),
            gp_Dir(0, 0, 1),
            gp_Dir(math.cos(axis_angle), math.sin(axis_angle), 0),
        ),
        radius1,
        radius2,
    )
    return _conic_shape(curve, angle, wire)


def interpolate_face(
    rows: tuple[tuple[Point3Value, ...], ...],
    degree_min: int,
    degree_max: int,
) -> ResolvedShape:
    if len(rows) < 2 or len(rows[0]) < 2:
        raise ValueError("interpolate2 requires at least a 2x2 point grid")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("interpolate2 point grid must be rectangular")
    points = TColgp_Array2OfPnt(1, len(rows), 1, width)
    for row_index, row in enumerate(rows, 1):
        for column_index, point in enumerate(row, 1):
            points.SetValue(row_index, column_index, _point(point))
    surface = GeomAPI_PointsToBSplineSurface(
        points,
        degree_min,
        degree_max,
        GeomAbs_C2,
        1e-3,
    )
    if not surface.IsDone():
        raise ValueError("interpolate2 surface construction failed")
    builder = BRepBuilderAPI_MakeFace(surface.Surface(), 1e-5)
    if not builder.IsDone():
        raise ValueError("interpolate2 face construction failed")
    return ResolvedShape(builder.Face())


def fix_face(shape: ResolvedShape) -> ResolvedShape:
    if shape.Shape().ShapeType() != TopAbs_FACE:
        raise TypeError("fix_face expects Face")
    fixer = ShapeFix_Face(as_face(shape.Shape()))
    fixer.Perform()
    fixer.FixOrientation()
    return ResolvedShape(fixer.Face())


def infinite_plane() -> ResolvedShape:
    builder = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)))
    if not builder.IsDone():
        raise ValueError("infinite plane construction failed")
    return ResolvedShape(builder.Face())


def ruled_face(first: ResolvedShape, second: ResolvedShape) -> ResolvedShape:
    if first.Shape().ShapeType() != TopAbs_EDGE:
        raise TypeError("ruled first argument must be Edge")
    if second.Shape().ShapeType() != TopAbs_EDGE:
        raise TypeError("ruled second argument must be Edge")
    return ResolvedShape(
        make_fill_face(as_edge(first.Shape()), as_edge(second.Shape()))
    )


def widewire(
    spine: ResolvedShape,
    radius: float,
    circled_joints: bool,
    circled_ends: bool,
) -> ResolvedShape:
    """Build the legacy planar wide-wire shape without a nested lazy graph."""
    if spine.Shape().ShapeType() not in (TopAbs_EDGE, TopAbs_WIRE):
        raise TypeError("widewire spine must be Edge or Wire")
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("widewire radius must be finite and positive")

    from zencad.geom.boolops import _union
    from zencad.geom.face import _circle, _wideedge
    from zencad.geom.unify import _unify

    edges = spine.edges()
    if not edges:
        raise ValueError("widewire spine must contain at least one Edge")

    last_p0 = None
    last_p1 = None
    faces: list[ResolvedShape] = []
    for edge in edges:
        face, last_p0, last_p1 = _wideedge(
            edge,
            radius,
            last_p0,
            last_p1,
            circled_joints=circled_joints,
        )
        faces.append(face)

    if circled_ends:
        start, finish = spine.endpoints()
        faces.append(_circle(radius).transform(move(start)))
        faces.append(_circle(radius).transform(move(finish)))

    result = _unify(_union(faces))
    if result.Shape().IsNull():
        raise ValueError("widewire construction produced a null shape")
    return result


def surface_map_curve2(
    surface: SurfaceValue,
    curve: Curve2Value,
) -> ResolvedShape:
    builder = BRepBuilderAPI_MakeEdge(
        curve2_to_ocp(curve),
        surface_to_ocp(surface),
    )
    if not builder.IsDone():
        raise ValueError("cannot map Curve2 onto Surface")
    edge = builder.Edge()
    build_curves_3d(edge)
    return ResolvedShape(edge)


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


def affine_transform(
    shape: ResolvedShape,
    value: AffineTransformValue,
) -> ResolvedShape:
    transformed = BRepBuilderAPI_GTransform(
        shape.Shape(), affine_to_ocp(value), True
    ).Shape()
    if transformed.IsNull():
        raise ValueError("affine transformation produced a null shape")
    return ResolvedShape(transformed)


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
        reduced = [
            union(work[index], work[-index - 1]) for index in range(pair_count)
        ]
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
    native = shape.Shape()
    if native.ShapeType() == TopAbs_EDGE:
        edge = as_edge(native)
        vertex = (
            TopExp.LastVertex_s(edge, True)
            if finish
            else TopExp.FirstVertex_s(edge, True)
        )
        point = ocp_vertex_point(vertex)
        return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))
    start, end = shape.endpoints()
    point = end if finish else start
    return Point3Value(float(point.x), float(point.y), float(point.z))


def curve_trimmed_edge(
    curve: CurveValue,
    start: float,
    end: float,
) -> ResolvedShape:
    lower, upper = sorted((start, end))
    edge = BRepBuilderAPI_MakeEdge(curve_to_ocp(curve), lower, upper).Edge()
    if edge.IsNull():
        raise ValueError("trimmed edge construction failed")
    if end < start:
        edge = as_edge(edge.Reversed())
    return ResolvedShape(edge)


def curve_edge(
    curve: CurveValue,
    interval: tuple[float, float] | None,
) -> ResolvedShape:
    native_curve = curve_to_ocp(curve)
    if interval is None:
        builder = BRepBuilderAPI_MakeEdge(native_curve)
    else:
        lower, upper = sorted(interval)
        builder = BRepBuilderAPI_MakeEdge(native_curve, lower, upper)
    if not builder.IsDone():
        raise ValueError("edge construction from Curve failed")
    edge = builder.Edge()
    if interval is not None and interval[1] < interval[0]:
        edge = as_edge(edge.Reversed())
    return ResolvedShape(edge)


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


def svg_elliptic_arc(
    start: Point3Value,
    end: Point3Value,
    radius_x: float,
    radius_y: float,
    x_axis_angle: float,
    large: bool,
    sweep: bool,
) -> ResolvedShape:
    """Build one SVG endpoint-parameterized elliptical arc."""
    radius_x = abs(radius_x)
    radius_y = abs(radius_y)
    if not math.isfinite(radius_x) or radius_x == 0:
        raise ValueError("SVG arc radius_x must be finite and non-zero")
    if not math.isfinite(radius_y) or radius_y == 0:
        raise ValueError("SVG arc radius_y must be finite and non-zero")
    if not math.isfinite(x_axis_angle):
        raise ValueError("SVG arc x_axis_angle must be finite")
    if abs(start.z - end.z) > 1e-9:
        raise ValueError("SVG arc endpoints must lie in one XY plane")
    if math.hypot(start.x - end.x, start.y - end.y) <= 1e-12:
        raise ValueError("SVG arc endpoints must be distinct")

    cosine = math.cos(x_axis_angle)
    sine = math.sin(x_axis_angle)
    half_dx = (start.x - end.x) / 2
    half_dy = (start.y - end.y) / 2
    local_x = cosine * half_dx + sine * half_dy
    local_y = -sine * half_dx + cosine * half_dy

    radii_scale = local_x * local_x / (radius_x * radius_x) + local_y * local_y / (
        radius_y * radius_y
    )
    if radii_scale > 1:
        scale = math.sqrt(radii_scale)
        radius_x *= scale
        radius_y *= scale

    numerator = (
        radius_x * radius_x * radius_y * radius_y
        - radius_x * radius_x * local_y * local_y
        - radius_y * radius_y * local_x * local_x
    )
    denominator = (
        radius_x * radius_x * local_y * local_y
        + radius_y * radius_y * local_x * local_x
    )
    if denominator <= 0:
        raise ValueError("cannot determine SVG arc center")
    sign = -1.0 if large == sweep else 1.0
    factor = sign * math.sqrt(max(0.0, numerator / denominator))
    center_local_x = factor * radius_x * local_y / radius_y
    center_local_y = -factor * radius_y * local_x / radius_x
    center_x = cosine * center_local_x - sine * center_local_y + (start.x + end.x) / 2
    center_y = sine * center_local_x + cosine * center_local_y + (start.y + end.y) / 2

    def vector_angle(ax: float, ay: float, bx: float, by: float) -> float:
        return math.atan2(ax * by - ay * bx, ax * bx + ay * by)

    unit_start_x = (local_x - center_local_x) / radius_x
    unit_start_y = (local_y - center_local_y) / radius_y
    unit_end_x = (-local_x - center_local_x) / radius_x
    unit_end_y = (-local_y - center_local_y) / radius_y
    start_parameter = vector_angle(1, 0, unit_start_x, unit_start_y)
    delta = vector_angle(
        unit_start_x,
        unit_start_y,
        unit_end_x,
        unit_end_y,
    )
    if sweep and delta < 0:
        delta += 2 * math.pi
    elif not sweep and delta > 0:
        delta -= 2 * math.pi

    major_radius = radius_x
    minor_radius = radius_y
    major_angle = x_axis_angle
    if radius_y > radius_x:
        major_radius, minor_radius = radius_y, radius_x
        major_angle += math.pi / 2
        start_parameter -= math.pi / 2
    ellipse = Geom_Ellipse(
        gp_Ax2(
            gp_Pnt(center_x, center_y, start.z),
            gp_Dir(0, 0, 1),
            gp_Dir(math.cos(major_angle), math.sin(major_angle), 0),
        ),
        major_radius,
        minor_radius,
    )
    end_parameter = start_parameter + delta
    lower, upper = sorted((start_parameter, end_parameter))
    builder = BRepBuilderAPI_MakeEdge(ellipse, lower, upper)
    if not builder.IsDone():
        raise ValueError("SVG elliptical arc construction failed")
    edge = builder.Edge()
    if delta < 0:
        edge = as_edge(edge.Reversed())
    return ResolvedShape(edge)


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


def offset_shape(shape: ResolvedShape, distance: float) -> ResolvedShape:
    algorithm = BRepOffsetAPI_MakeOffsetShape()
    algorithm.PerformByJoin(shape.Shape(), distance, 1e-6)
    algorithm.Build()
    if not algorithm.IsDone() or algorithm.Shape().IsNull():
        raise ValueError(f"offset failed for distance {distance}")
    return ResolvedShape(algorithm.Shape())


def thicksolid_shape(
    shape: ResolvedShape,
    thickness: float,
    references: tuple[Point3Value, ...],
) -> ResolvedShape:
    from zencad.geom.near import _near_face

    faces_to_remove = TopTools_ListOfShape()
    for reference in _legacy_points(references) or ():
        faces_to_remove.Append(_near_face(shape, reference).Face())
    algorithm = BRepOffsetAPI_MakeThickSolid()
    algorithm.MakeThickSolidByJoin(
        shape.Shape(),
        faces_to_remove,
        thickness,
        1e-3,
    )
    if not algorithm.IsDone() or algorithm.Shape().IsNull():
        raise ValueError(
            f"thicksolid failed for thickness {thickness} and "
            f"{len(references)} face references"
        )
    return ResolvedShape(algorithm.Shape())


def shapefix_solid_shape(shape: ResolvedShape) -> ResolvedShape:
    fixer = ShapeFix_Solid(as_solid(shape.Shape()))
    fixer.Perform()
    result = fixer.Solid()
    if result.IsNull():
        raise ValueError("shapefix_solid produced a null Solid")
    return ResolvedShape(result)


def unify_shape(shape: ResolvedShape) -> ResolvedShape:
    algorithm = ShapeUpgrade_UnifySameDomain(shape.Shape(), True, True, True)
    algorithm.Build()
    result = algorithm.Shape()
    if result.IsNull():
        raise ValueError("unify produced a null Shape")
    return ResolvedShape(result)


def sew_wire(
    shapes: tuple[ResolvedShape, ...],
    sort: bool,
) -> ResolvedShape:
    from zencad.geom.sew import _sew_wire

    try:
        result = _sew_wire(list(shapes), sort=sort)
    except Exception as error:
        raise ValueError(
            f"sew could not connect {len(shapes)} Edge/Wire operands"
        ) from error
    if result.Shape().IsNull():
        raise ValueError("sew produced a null Wire")
    return result


def sew_shell(shapes: tuple[ResolvedShape, ...]) -> ResolvedShape:
    faces: list[ResolvedShape] = []
    for shape in shapes:
        if shape.Shape().ShapeType() == TopAbs_FACE:
            faces.append(shape)
        else:
            faces.extend(shape.faces())
    try:
        return make_shell(tuple(faces))
    except Exception as error:
        raise ValueError(
            f"sew could not connect {len(shapes)} Face/Shell operands"
        ) from error


def _near_part(
    shape: ResolvedShape,
    point: Point3Value,
    kind: TopAbs_ShapeEnum,
    convert: Callable[[TopoDS_Shape], TopoDS_Shape],
    name: str,
) -> ResolvedShape:
    query_vertex = BRepBuilderAPI_MakeVertex(_point(point)).Vertex()
    explorer = TopExp_Explorer(shape.Shape(), kind)
    nearest: TopoDS_Shape | None = None
    minimum = math.inf
    while explorer.More():
        candidate = convert(explorer.Current())
        extrema = BRepExtrema_DistShapeShape(candidate, query_vertex)
        if extrema.IsDone() and extrema.Value() < minimum:
            nearest = candidate
            minimum = float(extrema.Value())
        explorer.Next()
    if nearest is None:
        raise ValueError(f"near_{name} found no {name} topology in Shape")
    return ResolvedShape(nearest)


def near_vertex(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_VERTEX, as_vertex, "vertex")


def near_edge(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_EDGE, as_edge, "edge")


def near_wire(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_WIRE, as_wire, "wire")


def near_face(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_FACE, as_face, "face")


def near_shell(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_SHELL, as_shell, "shell")


def near_solid(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_SOLID, as_solid, "solid")


def near_compsolid(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_COMPSOLID, as_compsolid, "compsolid")


def near_compound(shape: ResolvedShape, point: Point3Value) -> ResolvedShape:
    return _near_part(shape, point, TopAbs_COMPOUND, as_compound, "compound")


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
