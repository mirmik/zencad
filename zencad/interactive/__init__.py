from zencad.interactive.interactive_object import point3

from zencad.interactive.point import PointInteractiveObject
from zencad.interactive.axis import AxisInteractiveObject
from zencad.interactive.shape import ShapeInteractiveObject
from zencad.interactive.mesh import MeshInteractiveObject
from zencad.interactive.line import line, arrow
from zencad.interactive.interactive_object import InteractiveObject

from OCP.Geom import Geom_CartesianPoint
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

from zencad.axis import Axis
from zencad.color import Color
from zencad.geom.shape import Shape
from zencad.geom.mesh import MeshData


def create_interactive_object(obj, color=None, display_mode=None):
    if isinstance(obj, InteractiveObject):
        return obj

    if isinstance(color, (tuple, list)):
        color = Color(*color)

    if isinstance(obj, (
        TopoDS_Edge,
        TopoDS_Wire,
        TopoDS_Vertex,
        TopoDS_Face,
        TopoDS_Compound,
        TopoDS_CompSolid,
        TopoDS_Shell,
        TopoDS_Solid,
        TopoDS_Shape,
    )):
        obj = Shape(obj)

    if isinstance(obj, Shape):
        if display_mode is not None:
            raise ValueError("display_mode is only supported for MeshData")
        return ShapeInteractiveObject(obj, color)
    elif isinstance(obj, MeshData):
        return MeshInteractiveObject(obj, color, display_mode=display_mode)
    elif isinstance(obj, Axis):
        return AxisInteractiveObject(obj, color)
    elif isinstance(obj, (Geom_CartesianPoint, point3)):
        return PointInteractiveObject(obj, color)

    else:
        raise Exception("unresolved type", obj.__class__)


__all__ = [
    "line",
    "arrow"
]
