from OCP.TopAbs import TopAbs_VERTEX, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCP.TopoDS import TopoDS_Face, TopoDS_Edge, TopoDS_Wire, TopoDS_Vertex, TopoDS_Shell, TopoDS_Solid, TopoDS_Compound, TopoDS_CompSolid
from zencad.occ_compat import as_compound, as_compsolid, as_edge, as_face, as_shell, as_solid, as_vertex, as_wire


class shape_type:
    def __init__(self, convert, construct):
        self.convert = convert
        self.construct = construct


shape_types = {
    TopAbs_FACE: shape_type(convert=as_face, construct=TopoDS_Face),
    TopAbs_VERTEX: shape_type(convert=as_vertex, construct=TopoDS_Vertex),
    TopAbs_WIRE: shape_type(convert=as_wire, construct=TopoDS_Wire),
    TopAbs_EDGE: shape_type(convert=as_edge, construct=TopoDS_Edge),
    TopAbs_SOLID: shape_type(convert=as_solid, construct=TopoDS_Solid),
    TopAbs_SHELL: shape_type(convert=as_shell, construct=TopoDS_Shell),
    TopAbs_COMPOUND: shape_type(convert=as_compound, construct=TopoDS_Compound),
    TopAbs_COMPSOLID: shape_type(convert=as_compsolid, construct=TopoDS_CompSolid),
}
