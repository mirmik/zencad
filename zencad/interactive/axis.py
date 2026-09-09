from zencad.interactive.interactive_object import InteractiveObject

from OCP.AIS import AIS_Line
from OCP.Aspect import Aspect_TOL_DASH


class AxisInteractiveObject(InteractiveObject):
    def __init__(self, axis, color):
        self.axis = axis
        line = AIS_Line(axis.to_Geom_Line())
        line.SetInfiniteState(True)
        super().__init__(line, color=color)
        line.Attributes().LineAspect().SetTypeOfLine(Aspect_TOL_DASH)
