from zencad.interactive.interactive_object import InteractiveObject

from OCP.AIS import AIS_Axis


class AxisInteractiveObject(InteractiveObject):
    def __init__(self, axis, color):
        self.axis = axis
        super().__init__(AIS_Axis(axis.to_gp_Ax1()), color=color)
