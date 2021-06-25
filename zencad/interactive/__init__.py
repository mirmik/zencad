from zencad.interactive.interactive_object import point3

from zencad.interactive.point import PointInteractiveObject
from zencad.interactive.axis import AxisInteractiveObject
from zencad.interactive.shape import ShapeInteractiveObject
from zencad.interactive.line import line, arrow
from zencad.interactive.interactive_object import InteractiveObject

from OCC.Core.Geom import Geom_CartesianPoint
import OCC.Core

from zencad.axis import Axis
from zencad.color import Color
from zencad.geom.shape import Shape


def create_interactive_object(obj, color=None):
    if isinstance(obj, InteractiveObject):
        return obj

    if isinstance(color, (tuple, list)):
        color = Color(*color)

    if isinstance(obj, (
        OCC.Core.TopoDS.TopoDS_Edge,
        OCC.Core.TopoDS.TopoDS_Wire,
        OCC.Core.TopoDS.TopoDS_Vertex,
        OCC.Core.TopoDS.TopoDS_Face,
        OCC.Core.TopoDS.TopoDS_Compound,
        OCC.Core.TopoDS.TopoDS_CompSolid,
        OCC.Core.TopoDS.TopoDS_Shell,
        OCC.Core.TopoDS.TopoDS_Solid,
        OCC.Core.TopoDS.TopoDS_Shape
    )):
        obj = Shape(obj)

    if isinstance(obj, Shape):
        return ShapeInteractiveObject(obj, color)
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
