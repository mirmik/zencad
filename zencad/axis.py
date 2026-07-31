import zencad.util
from OCP.Geom import Geom_Line
from OCP.gp import gp_Ax1, gp_Lin, gp_Pnt, gp_Dir, gp_XYZ


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

    def to_gp_Ax1(self):
        return gp_Ax1(
            gp_Pnt(0, 0, 0),
            gp_Dir(*self._coords),
        )
