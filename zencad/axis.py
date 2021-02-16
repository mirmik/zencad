import zencad.util
from OCC.Core.Geom import Geom_Line
from OCC.Core.gp import gp_Lin, gp_Pnt, gp_Dir, gp_XYZ


class Axis:
    def __init__(self, *xyz):
        self._coords = zencad.util.as_indexed(xyz)

    def to_Geom_Line(self):
        return Geom_Line(
            gp_Lin(
                gp_Pnt(0, 0, 0),
                gp_Dir(
                    gp_XYZ(
                        self._coords[0],
                        self._coords[1],
                        self._coords[2]))))
