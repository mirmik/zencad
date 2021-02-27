from OCC.Core.AIS import AIS_InteractiveObject, AIS_Shape, AIS_Axis, AIS_Point
from OCC.Core.Prs3d import Prs3d_LineAspect
from OCC.Core.Quantity import Quantity_NOC_BLACK, Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Aspect import Aspect_TOL_SOLID
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.Geom import Geom_CartesianPoint
from OCC.Core.TopLoc import TopLoc_Location

from zencad.shape import Shape
from zencad.color import Color, default_color, default_wire_color
from zencad.axis import Axis
from zencad.geom.trans import Transformation
from zencad.geom.exttrans import nulltrans
import zencad.geom.transformable


class InteractiveObject(zencad.geom.transformable.Transformable):
    def __init__(self, iobj, color, border_color=None, wire_color=None):
        self.ais_object = iobj
        self._location = nulltrans()
        self._context = None
        if border_color is None:
            border_color = color

        self.set_color(
            color=color,
            border_color=border_color,
            wire_color=wire_color)

    def set_color(self, color, border_color=None, wire_color=None):
        if color is None:
            color = default_color()
        if wire_color is None:
            wire_color = default_wire_color()
        if border_color is None:
            border_color = Color(0, 0, 0)

        self.color = color
        self.border_color = border_color
        self.wire_color = wire_color

        self.ais_object.SetColor(self.color.to_Quantity_Color())
        self.ais_object.SetTransparency(self.color.a)

        aspect = self.ais_object.Attributes().LineAspect()
        aspect.SetColor(self.border_color.to_Quantity_Color())
        self.ais_object.Attributes().SetFaceBoundaryAspect(aspect)

        aspect = self.ais_object.Attributes().WireAspect()
        aspect.SetColor(self.wire_color.to_Quantity_Color())
        self.ais_object.Attributes().SetWireAspect(aspect)

    def relocate(self, trsf):
        self._location = trsf
        if self._context:
            loc = TopLoc_Location(trsf._trsf)
            self._context.SetLocation(self.ais_object, loc)

    def location(self):
        if self._context:
            return Transformation(self._context.Location(self.ais_object).Transformation())
        else:
            return self._location

    def transform(self, trans):
        self.relocate(self.location() * trans)
        return self

    def bind_context(self, context):
        self._context = context
        self.relocate(self._location)

    def hide(self, en):
        if self._context:
            if en:
                self._context.Erase(self.ais_object, False)
            else:
                self._context.Display(self.ais_object, False)


class ShapeInteractiveObject(InteractiveObject):
    def __init__(self, shape, color, border_color=Color(0, 0, 0), wire_color=None):
        self.shape = shape
        super().__init__(AIS_Shape(self.shape._shp),
                         color=color,
                         border_color=border_color,
                         wire_color=wire_color)


class AxisInteractiveObject(InteractiveObject):
    def __init__(self, axis, color):
        self.axis = axis
        super().__init__(AIS_Axis(axis.to_Geom_Line()), color=color)


class PointInteractiveObject(InteractiveObject):
    def __init__(self, point, color):
        self.point = point
        super().__init__(AIS_Point(point), color=color)


def create_interactive_object(obj, color=None):
    if isinstance(color, (tuple, list)):
        color = Color(*color)

    if isinstance(obj, Shape):
        return ShapeInteractiveObject(obj, color)
    elif isinstance(obj, Axis):
        return AxisInteractiveObject(obj, color)
    elif isinstance(obj, Geom_CartesianPoint):
        return PointInteractiveObject(obj, color)

    else:
        raise Exception("unresolved type", obj.__class__)
