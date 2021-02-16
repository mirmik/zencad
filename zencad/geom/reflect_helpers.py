from OCC.Core.TopAbs import TopAbs_VERTEX, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCC.Core.TopoDS import TopoDS_Face, TopoDS_Edge, TopoDS_Wire, TopoDS_Vertex, topods, TopoDS_Shell, TopoDS_Solid, TopoDS_Compound, TopoDS_CompSolid


class shape_type:
    def __init__(self, convert, construct):
        self.convert = convert
        self.construct = construct


shape_types = {
    TopAbs_FACE: shape_type(convert=topods.Face, construct=TopoDS_Face),
    TopAbs_VERTEX: shape_type(convert=topods.Vertex, construct=TopoDS_Vertex),
    TopAbs_WIRE: shape_type(convert=topods.Wire, construct=TopoDS_Wire),
    TopAbs_EDGE: shape_type(convert=topods.Edge, construct=TopoDS_Edge),
    TopAbs_SOLID: shape_type(convert=topods.Solid, construct=TopoDS_Solid),
    TopAbs_SHELL: shape_type(convert=topods.Shell, construct=TopoDS_Shell),
    TopAbs_COMPOUND: shape_type(convert=topods.Compound, construct=TopoDS_Compound),
    TopAbs_COMPSOLID: shape_type(convert=topods.CompSolid, construct=TopoDS_CompSolid),
}
