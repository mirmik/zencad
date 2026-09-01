from zencad._eager import eager
from zencad.geom.shape import Shape, nocached_shape_generator, shape_generator

from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeFillet2d
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepAdaptor import BRepAdaptor_Surface as _BRepAdaptor_Surface
from OCP.BRepOffsetAPI import BRepOffsetAPI_DraftAngle as _BRepOffsetAPI_DraftAngle
from OCP.GeomAbs import GeomAbs_Plane as _GeomAbs_Plane
from OCP.gp import gp_Dir as _gp_Dir, gp_Pln as _gp_Pln, gp_Pnt as _gp_Pnt

from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location
from zencad.occ_compat import face_triangulation
from zencad.geom.near import _near_vertex
from zencad.util import *

import itertools
import math as _math
import sys

def _restore_shapetype(shp):
    if len(shp.solids()) == 1:
        return shp.solids()[0]

    if len(shp.shells()) == 1:
        return shp.shells()[0]

    elif len(shp.faces()) == 1:
        return shp.faces()[0]

    elif len(shp.wires()) == 1:
        return shp.wires()[0]

    elif len(shp.edges()) == 1:
        return shp.edges()[0]

    return shp


@eager.decorator(cls=shape_generator)
def restore_shapetype(shp):
    return _restore_shapetype(shp)


def _fillet(shp, r, refs=None):
    if (shp.shapetype() == "face"):
        return _fillet2d(shp, r, refs)

    edge_refs = _operation_edge_references(shp, refs, "fillet")
    if refs and edge_refs is None:
        refs = points(refs)

    if shp.is_solid() or shp.is_compound() or shp.is_compsolid():
        mk = BRepFilletAPI_MakeFillet(shp.Shape())

        if edge_refs is not None:
            for edge in edge_refs:
                mk.Add(r, edge.Edge())
        elif refs:
            for p in refs:
                minimum = float("inf")
                vtx = p.Vtx()

                for edg in shp.edges():
                    extrema = BRepExtrema_DistShapeShape(edg.Edge(), vtx)

                    if minimum > extrema.Value():
                        ret = edg
                        minimum = extrema.Value()

                mk.Add(r, ret.Edge())
        else:
            for edg in shp.edges():
                mk.Add(r, edg.Edge())

        return Shape(mk.Shape())
    else:
        raise Exception("Fillet argument has unsuported type.")


def _chamfer(shp, r, refs=None):
    edge_refs = _operation_edge_references(shp, refs, "chamfer")
    if refs and edge_refs is None:
        refs = points(refs)

    if shp.is_solid() or shp.is_compound() or shp.is_compsolid():
        mk = BRepFilletAPI_MakeChamfer(shp.Shape())

        if edge_refs is not None:
            for edge in edge_refs:
                mk.Add(r, edge.Edge())
        elif refs:
            for p in refs:
                minimum = float("inf")
                vtx = p.Vtx()

                for edg in shp.edges():
                    extrema = BRepExtrema_DistShapeShape(edg.Edge(), vtx)

                    if minimum > extrema.Value():
                        ret = edg
                        minimum = extrema.Value()

                mk.Add(r, ret.Edge())
        else:
            for edg in shp.edges():
                mk.Add(r, edg.Edge())

        return Shape(mk.Shape())
    else:
        raise Exception("Fillet argument has unsuported type.")


def _operation_edge_references(shp, refs, name):
    if not refs:
        return None
    refs = tuple(refs)
    shape_refs = tuple(isinstance(ref, Shape) for ref in refs)
    if not any(shape_refs):
        return None
    if not all(shape_refs) or not all(ref.is_edge() for ref in refs):
        raise TypeError(f"{name} references must be all points or all Edges")
    body_edges = shp.edges()
    selected = []
    for index, reference in enumerate(refs, 1):
        match = next(
            (edge for edge in body_edges if edge.Edge().IsSame(reference.Edge())),
            None,
        )
        if match is None:
            raise ValueError(f"{name} Edge reference {index} does not belong to body")
        if not any(edge.Edge().IsSame(match.Edge()) for edge in selected):
            selected.append(match)
    return selected


@eager.decorator(cls=shape_generator)
def chamfer(shp, r, refs=None):
    return _chamfer(shp, r, refs)


@eager.decorator(cls=shape_generator)
def fillet(shp, r, refs=None):
    return _fillet(shp, r, refs)


def _fillet2d(shp, r, refs=None):
    mk = BRepFilletAPI_MakeFillet2d(shp.Face())

    if refs is None:
        refs = shp.vertices()

    for p in refs:
        mk.AddFillet(_near_vertex(shp, p).Vertex(), r)

    return Shape(mk.Shape())


@eager.decorator(cls=shape_generator)
def fillet2d(shp, r, refs=None):
    return _fillet2d(shp, r, refs)


def _draft_coordinates(value, name):
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


def _draft_direction(value):
    try:
        return _gp_Dir(*_draft_coordinates(value, "draft direction"))
    except Exception as error:
        raise ValueError("draft direction must be non-zero") from error


def _draft_neutral_plane(value, direction):
    if value is None:
        return _gp_Pln(_gp_Pnt(0, 0, 0), direction)
    if isinstance(value, Shape):
        if not value.is_face():
            raise TypeError("draft neutral Shape must be a planar face")
        adaptor = _BRepAdaptor_Surface(value.Face())
        if adaptor.GetType() != _GeomAbs_Plane:
            raise TypeError("draft neutral Shape must be a planar face")
        return adaptor.Plane()
    try:
        origin, normal = value
    except (TypeError, ValueError) as error:
        raise TypeError(
            "draft neutral must be a planar face or (origin, normal)"
        ) from error
    origin = _draft_coordinates(origin, "draft neutral origin")
    normal = _draft_coordinates(normal, "draft neutral normal")
    try:
        return _gp_Pln(_gp_Pnt(*origin), _gp_Dir(*normal))
    except Exception as error:
        raise ValueError("draft neutral normal must be non-zero") from error


def _draft(shp, faces, angle, direction=(0, 0, 1), neutral=None):
    if not isinstance(shp, Shape) or not shp.is_solid():
        raise TypeError("draft body must be a solid Shape")
    if isinstance(faces, Shape):
        faces = (faces,)
    else:
        try:
            faces = tuple(faces)
        except TypeError as error:
            raise TypeError("draft faces must be a Face or an iterable of Faces") from error
    if not faces:
        raise ValueError("draft requires at least one face")
    if not all(isinstance(face, Shape) and face.is_face() for face in faces):
        raise TypeError("draft faces must contain only Face shapes")

    angle = float(angle)
    if not _math.isfinite(angle) or angle == 0:
        raise ValueError("draft angle must be finite and non-zero")
    if abs(angle) >= _math.pi / 2:
        raise ValueError("draft angle magnitude must be less than pi/2")

    direction = _draft_direction(direction)
    neutral_plane = _draft_neutral_plane(neutral, direction)
    algorithm = _BRepOffsetAPI_DraftAngle(shp.Shape())
    for index, face in enumerate(faces, 1):
        try:
            algorithm.Add(
                face.Face(),
                direction,
                angle,
                neutral_plane,
            )
        except Exception as error:
            raise ValueError(f"draft rejected face {index}: {error}") from error
        if not algorithm.AddDone():
            raise ValueError(
                f"draft rejected face {index}: OCCT status {algorithm.Status()}"
            )

    algorithm.Build()
    if not algorithm.IsDone():
        raise ValueError(f"draft construction failed: OCCT status {algorithm.Status()}")
    result = Shape(algorithm.Shape())
    if not result.is_solid():
        raise ValueError("draft construction did not produce a solid")
    return result


@eager.decorator(cls=shape_generator)
def draft(shp, faces, angle, direction=(0, 0, 1), neutral=None):
    """Taper selected faces around a neutral plane.

    Along ``direction``, a positive ``angle`` removes material and a negative
    angle adds it. ``neutral`` defaults to the origin plane normal to the pull
    direction and also accepts a planar Face or ``(origin, normal)``.
    """

    return _draft(shp, faces, angle, direction, neutral)

def get_nodes(triangulation):
    if hasattr(triangulation, "Nodes"):
        return triangulation.Nodes()
    else:
        return triangulation.InternalNodes()

def get_triangles(triangulation):
    if hasattr(triangulation, "Triangles"):
        return triangulation.Triangles()
    else:
        return triangulation.InternalTriangles()

def _triangulate_face(shp, deflection):
    mesh = BRepMesh_IncrementalMesh(shp.Shape(), deflection)

    reverse_orientation = shp.Face().Orientation() == TopAbs_REVERSED

    L = TopLoc_Location()
    triangulation = face_triangulation(shp.Face(), L)

    Nodes = get_nodes(triangulation)
    Triangles = get_triangles(triangulation)

    triangles = []
    for i in range(1, triangulation.NbTriangles() + 1):
        tri = Triangles.Value(i)
        a, b, c = tri.Get()

        if reverse_orientation:
            triangles.append((b-1, a-1, c-1))
        else:
            triangles.append((a-1, b-1, c-1))

    nodes = []

    # if python3.10 or higher:
    if sys.version_info >= (3, 10):
        for i in range(0, triangulation.NbNodes()):
            nodes.append(point3(Nodes.Value(i)))
    else:
        for i in range(1, triangulation.NbNodes() + 1):
            nodes.append(point3(Nodes.Value(i)))

    return nodes, triangles


@eager.decorator(cls=shape_generator)
def triangulate_face(shp, deflection):
    return _triangulate_face(shp, deflection)


def _triangulate(shp, deflection):
    results = []
    nodes = []
    triangles = []

    for f in shp.faces():
        results.append(_triangulate_face(f, deflection))

    for r in results:
        nsize = len(nodes)
        nodes.extend(r[0])

        for t in r[1]:
            triangles.append([t[0]+nsize, t[1]+nsize, t[2]+nsize])

    return nodes, triangles


@eager
def triangulate(shp, deflection):
    return _triangulate(shp, deflection)
