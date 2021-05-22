from OCC.Core.AIS import AIS_InteractiveObject, AIS_Shape, AIS_Axis, AIS_Point
from OCC.Core.Prs3d import Prs3d_LineAspect
from OCC.Core.Quantity import Quantity_NOC_BLACK, Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Aspect import Aspect_TOL_SOLID, Aspect_TOD_ABSOLUTE
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.Geom import Geom_CartesianPoint
from OCC.Core.Prs3d import Prs3d_Drawer
from OCC.Core.TopLoc import TopLoc_Location
import OCC.Core

from zencad.geom.shape import Shape
from zencad.color import Color, default_color, default_wire_color
from zencad.axis import Axis
from zencad.geom.trans import Transformation
from zencad.geom.exttrans import nulltrans
from zencad.geom.transformable import Transformable
from zencad.interactive.displayable import Displayable
from zencad.util import point3
from zencad.settings import Settings


class InteractiveObject(Transformable, Displayable):
    def __init__(self, iobj, color, border_color=None, wire_color=None):
        self.ais_object = iobj
        self._location = nulltrans()
        self._hide = False
        self._context = None
        if border_color is None:
            border_color = color

        self.setup_drawer()

        self.set_color(
            color=color,
            border_color=border_color,
            wire_color=wire_color)

    def setup_drawer(self):
        drawer = self.ais_object.Attributes()
        drawer.SetFaceBoundaryDraw(True)
        drawer.SetTypeOfDeflection(Aspect_TOD_ABSOLUTE)

        deviation = Settings.get(["view", "default_chordial_deviation"])
        drawer.SetMaximalChordialDeviation(deviation)

    def bind_to_scene(self, scene):
        scene.add_interactive_object(self)

    def set_color(self, color, b=None, c=None, d=0, border_color=None, wire_color=None):
        if b is not None and c is not None:
            color = Color(color, b, c, d)

        if color is None:
            color = default_color()
        if wire_color is None:
            wire_color = default_wire_color()
        if border_color is None:
            border_color = Color(0, 0, 0)

        self._color = color
        self._border_color = border_color
        self._wire_color = wire_color

        self.ais_object.SetColor(self._color.to_Quantity_Color())
        self.ais_object.SetTransparency(self._color.a)

        aspect = self.ais_object.Attributes().LineAspect()
        aspect.SetColor(self._border_color.to_Quantity_Color())
        self.ais_object.Attributes().SetFaceBoundaryAspect(aspect)

        aspect = self.ais_object.Attributes().WireAspect()
        aspect.SetColor(self._wire_color.to_Quantity_Color())
        self.ais_object.Attributes().SetWireAspect(aspect)

    def relocate(self, trsf):
        self._location = trsf
        if self._context:
            loc = TopLoc_Location(trsf._trsf)
            self._context.SetLocation(self.ais_object, loc)

    def color(self):
        return self._color

    def location(self):
        if self._context:
            return Transformation(self._context.Location(self.ais_object).Transformation())
        else:
            return self._location

    def transform(self, trans):
        self.relocate(trans * self.location())
        return self

    def bind_context(self, context):
        self._context = context
        self.relocate(self._location)
        self.hide(self._hide)
        self._context.Update(self.ais_object, True)

    def hide(self, en):
        self._hide = en
        if self._context:
            if en:
                self._context.Erase(self.ais_object, False)
            else:
                self._context.Display(self.ais_object, False)
