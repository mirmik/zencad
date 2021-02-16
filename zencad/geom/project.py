from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnCurve
from zencad.util import to_Pnt, point3


def project_point_on_curve(pnt, crv):
    algo = GeomAPI_ProjectPointOnCurve(to_Pnt(pnt), crv.Curve())
    return point3(algo.NearestPoint())


def project(pnt, tgt):
    return project_point_on_curve(pnt, tgt)
