from OCP.Aspect import Aspect_TOD_ABSOLUTE
from OCP.TopLoc import TopLoc_Location

from zencad._native.shape import Shape
from zencad.color import Color, default_color, default_wire_color, default_border_color
from zencad.axis import Axis
from zencad._native.trans import Transformation
from zencad._native.exttrans import nulltrans
from zencad._native.transformable import Transformable
from zencad.interactive.displayable import Displayable
from zencad.util import point3
from zencad.settings import Settings

from zencad.bbox import BoundaryBox


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

    def redisplay(self):
        self.ais_object.Redisplay()

    def setup_drawer(self):
        drawer = self.ais_object.Attributes()
        drawer.SetFaceBoundaryDraw(True)
        drawer.SetTypeOfDeflection(Aspect_TOD_ABSOLUTE)

        deviation = Settings.get(["view", "default_chordial_deviation"])
        drawer.SetMaximalChordialDeviation(deviation)

    def bind_to_scene(self, scene):
        scene.add_interactive_object(self)

    def set_border_width(self, width):
        #drawer = self.ais_object.Attributes()
        #drawer.SetWidth(width)
        raise Exception("Not implemented")

    def set_color(self, color, b=None, c=None, d=0, border_color=None, wire_color=None):
        if b is not None and c is not None:
            color = Color(color, b, c, d)

        if color is None:
            color = default_color()
        if wire_color is None:
            wire_color = default_wire_color()
        if border_color is None:
            border_color = default_border_color()

        self._color = color
        self._border_color = border_color
        self._wire_color = wire_color

        self.ais_object.SetColor(self._color.to_Quantity_Color())
        self.ais_object.SetTransparency(self._color.a)

        aspect = self.ais_object.Attributes().LineAspect()
        if aspect is not None:
            aspect.SetColor(self._border_color.to_Quantity_Color())
            self.ais_object.Attributes().SetFaceBoundaryAspect(aspect)

        aspect = self.ais_object.Attributes().WireAspect()
        if aspect is not None:
            aspect.SetColor(self._wire_color.to_Quantity_Color())
            self.ais_object.Attributes().SetWireAspect(aspect)

    def relocate(self, trsf):
        from zencad.geom.transforms import Transform

        if isinstance(trsf, Transform):
            trsf = Transformation(trsf.to_ocp())
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

    def bind_context(self, context, update=True):
        self._context = context
        self.relocate(self._location)
        self.hide(self._hide)
        self._context.Update(self.ais_object, update)

    def hide(self, en):
        self._hide = en
        if self._context:
            if en:
                self._context.Erase(self.ais_object, False)
            else:
                self._context.Display(self.ais_object, False)

    def boundbox(self):
        return BoundaryBox()
