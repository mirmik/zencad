from OCC.Core.TopExp import topexp, TopExp_Explorer
from OCC.Core.GeomAbs import GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse, GeomAbs_Hyperbola, GeomAbs_Parabola, GeomAbs_BezierCurve, GeomAbs_OffsetCurve, GeomAbs_BSplineCurve, GeomAbs_OtherCurve
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnCurve
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.TopoDS import TopoDS_Vertex

from zencad.util import to_numpy, point3, vector3


class CurveAlgo:
    def curvetype(self):
        adaptor = self.AdaptorCurve()
        type = adaptor.GetType()

        if type == GeomAbs_Line:
            return "line"
        if type == GeomAbs_Circle:
            return "circle"
        if type == GeomAbs_Ellipse:
            return "ellipse"
        if type == GeomAbs_Hyperbola:
            return "hyperbola"
        if type == GeomAbs_Parabola:
            return "parabola"
        if type == GeomAbs_BezierCurve:
            return "bezier"
        if type == GeomAbs_BSplineCurve:
            return "bspline"
        if type == GeomAbs_OffsetCurve:
            return "offset"
        if type == GeomAbs_OtherCurve:
            return "other"
        raise Exception("undefined curvetype")

    def d0(self, arg):
        assert(self.is_edge())
        adaptor = self.AdaptorCurve()
        pnt = gp_Pnt()
        self.AdaptorCurve().D0(arg, pnt)
        return point3(pnt.X(), pnt.Y(), pnt.Z())

    def value(self, arg):
        return self.d0(arg)

    def d1(self, arg):
        assert(self.is_edge())
        adaptor = self.AdaptorCurve()
        pnt, vec = gp_Pnt(), gp_Vec()
        self.AdaptorCurve().D1(arg, pnt, vec)
        return vector3((vec.X(), vec.Y(), vec.Z()))

    def range(self):
        adaptor = self.AdaptorCurve()
        return adaptor.FirstParameter(), adaptor.LastParameter()

    def endpoints(self):
        """Get tuple of start and finish point of current curve object 
           (if it exists)."""

        assert(self.is_wire_or_edge())

        if self.is_wire():
            a, b = TopoDS_Vertex(), TopoDS_Vertex()
            topexp.Vertices(self.Wire(), a, b)
            return point3(a), point3(b)

        elif self.is_edge():
            a = topexp.FirstVertex(self.Edge())
            b = topexp.LastVertex(self.Edge())
            return point3(a), point3(b)

    def line_parameters(self):
        if self.curvetype() != "line":
            raise Exception("curve is not line")

        o = self.AdaptorCurve().Line()

        return o.Location(), o.Direction()

    def circle_parameters(self):
        if self.curvetype() != "circle":
            raise Exception("curve is not circle")

        o = self.AdaptorCurve().Circle()
        p = o.Position()

        return (
            point3(p.Location()),
            o.Radius(),
            vector3(p.XDirection()),
            vector3(p.YDirection())
        )

    def ellipse_parameters(self):
        if self.curvetype() != "ellipse":
            raise Exception("curve is not ellipse")

        o = self.AdaptorCurve().Ellipse()
        p = o.Position()

        return (
            point3(p.Location()),
            o.MajorRadius(),
            o.MinorRadius(),
            vector3(p.XDirection()),
            vector3(p.YDirection())
        )

    def lower_distance_parameter(self, pnt):
        """Evalute parameter of curve's point that has 
           minimal distance to pnt"""

        algo = GeomAPI_ProjectPointOnCurve(pnt.Pnt(), self.Curve())
        return algo.LowerDistanceParameter()

    def trimmed_edge(self, start, finish):
        import zencad.geom.shape
        algo = BRepBuilderAPI_MakeEdge(self.Curve(), start, finish)
        return zencad.geom.shape.Shape(algo.Edge())
