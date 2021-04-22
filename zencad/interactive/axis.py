from zencad.interactive.interactive_object import InteractiveObject

from OCC.Core.AIS import AIS_Axis


class AxisInteractiveObject(InteractiveObject):
    def __init__(self, axis, color):
        self.axis = axis
        super().__init__(AIS_Axis(axis.to_Geom_Line()), color=color)
