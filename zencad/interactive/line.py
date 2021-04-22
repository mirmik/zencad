from zencad.interactive.interactive_object import InteractiveObject
from zencad.color import Color as color
from zencad.util import to_Pnt, to_Vec, point3

from OCC.Core.Geom import Geom_CartesianPoint
from OCC.Core.Prs3d import Prs3d_Drawer, Prs3d_ArrowAspect, Prs3d_LineAspect
from OCC.Core.AIS import AIS_Line
from OCC.Core.Aspect import Aspect_TOL_SOLID


class LineInteractiveObject(InteractiveObject):
    def __init__(self, p1, p2, width, color):
        self.p1 = point3(p1)
        self.p2 = point3(p2)

        super().__init__(self.make_ais(), color)

        self.width = width if width else 1
        self.set_line_aspect(self.width)

    def make_ais(self):
        p1 = Geom_CartesianPoint(to_Pnt(self.p1))
        p2 = Geom_CartesianPoint(to_Pnt(self.p2))
        return AIS_Line(p1, p2)

    def set_points(self, p1, p2):
        self.p1 = point3(p1)
        self.p2 = point3(p2)
        p1 = Geom_CartesianPoint(to_Pnt(self.p1))
        p2 = Geom_CartesianPoint(to_Pnt(self.p2))
        self.ais_object.SetPoints(p1, p2)

    def set_line_aspect(self, width, aspect_type=Aspect_TOL_SOLID):
        self.width = width

        lineAspect = Prs3d_LineAspect(
            self._color.to_Quantity_Color(),
            aspect_type,
            self.width)

        self.ais_object.Attributes().SetLineAspect(lineAspect)

    def set_arrow_aspect(self, arrlen):
        arrowAspect = Prs3d_ArrowAspect()
        arrowAspect.SetLength(arrlen)
        self.ais_object.Attributes().SetArrowAspect(arrowAspect)
        self.ais_object.Attributes().SetLineArrowDraw(True)


def line(p1, p2, color=color(1, 1, 1), width=1) -> LineInteractiveObject:
    iobj = LineInteractiveObject(p1, p2, color=color, width=width)
    return iobj


def arrow(p1, p2, color=color(1, 1, 1), arrlen=1, width=1) -> LineInteractiveObject:
    iobj = LineInteractiveObject(p1, p2, color=color, width=width)
    iobj.set_arrow_aspect(arrlen)
    return iobj
