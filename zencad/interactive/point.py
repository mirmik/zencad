from zencad.interactive.interactive_object import InteractiveObject

from OCC.Core.Geom import Geom_CartesianPoint
from OCC.Core.AIS import AIS_Point

from zencad.geombase import point3


class PointInteractiveObject(InteractiveObject):
    def __init__(self, point, color):
        if isinstance(point, point3):
            pnt = point.Pnt()
            point = Geom_CartesianPoint(pnt)

        self.point = point
        super().__init__(AIS_Point(point), color=color)
