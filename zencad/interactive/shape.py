from zencad.interactive.interactive_object import InteractiveObject
from zencad.color import Color

from OCC.Core.AIS import AIS_Shape


class ShapeInteractiveObject(InteractiveObject):
    def __init__(self, shape, color, border_color=Color(0, 0, 0), wire_color=None):
        self.shape = shape
        super().__init__(AIS_Shape(self.shape._shp),
                         color=color,
                         border_color=border_color,
                         wire_color=wire_color)
