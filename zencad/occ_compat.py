"""Small compatibility boundary for the cadquery-ocp migration.

Only pythonocc APIs that do not have a direct OCP spelling belong here.
Regular OCCT classes should be imported from their ``OCP`` modules directly.
"""

try:
    import OCP
    from OCP.BRep import BRep_Builder
    from OCP.BRep import BRep_Tool
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
    from OCP.BRepFill import BRepFill
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepLib import BRepLib
    from OCP.BRepTools import BRepTools
    from OCP.Precision import Precision
    from OCP.Standard import Standard_DomainError, Standard_Failure
    from OCP.TopExp import TopExp
    from OCP.TopoDS import TopoDS
    from OCP.gp import gp
except ImportError as exception:
    raise ImportError(
        "ZenCad requires a compatible OCP backend; install cadquery-ocp-novtk"
    ) from exception

BACKEND_NAME = "OCP"
try:
    BACKEND_VERSION = OCP.__version__
except AttributeError as exception:
    raise ImportError(
        "ZenCad found an incompatible OCP backend without version metadata; "
        "install cadquery-ocp-novtk"
    ) from exception


def as_vertex(shape):
    return TopoDS.Vertex(shape)


def as_edge(shape):
    return TopoDS.Edge(shape)


def as_wire(shape):
    return TopoDS.Wire(shape)


def as_face(shape):
    return TopoDS.Face(shape)


def as_shell(shape):
    return TopoDS.Shell(shape)


def as_solid(shape):
    return TopoDS.Solid(shape)


def as_compound(shape):
    return TopoDS.Compound(shape)


def as_compsolid(shape):
    return TopoDS.CompSolid(shape)


def add_to_bounds(shape, bounds):
    return BRepBndLib.Add_s(shape, bounds)


def make_fill_face(edge_a, edge_b):
    return BRepFill.Face_s(edge_a, edge_b)


def surface_properties(shape, properties):
    return BRepGProp.SurfaceProperties_s(shape, properties)


def volume_properties(shape, properties):
    return BRepGProp.VolumeProperties_s(shape, properties)


def build_curves_3d(shape):
    return BRepLib.BuildCurves3d_s(shape)


def read_brep(shape, path, builder=None):
    if builder is None:
        builder = BRep_Builder()
    source = str(path) if isinstance(path, (str, bytes)) or hasattr(path, "__fspath__") else path
    return BRepTools.Read_s(shape, source, builder)


def write_brep(shape, path):
    target = str(path) if isinstance(path, (str, bytes)) or hasattr(path, "__fspath__") else path
    return BRepTools.Write_s(shape, target)


def confusion():
    return Precision.Confusion_s()


def first_vertex(edge, cum_orientation=False):
    return TopExp.FirstVertex_s(edge, cum_orientation)


def last_vertex(edge, cum_orientation=False):
    return TopExp.LastVertex_s(edge, cum_orientation)


def wire_vertices(wire, first, last):
    return TopExp.Vertices_s(wire, first, last)


def direction_z():
    return gp.DZ_s()


def plane_xoy():
    return gp.XOY_s()


def make_sewing(*args, **kwargs):
    return BRepBuilderAPI_Sewing(*args, **kwargs)


def vertex_point(vertex):
    return BRep_Tool.Pnt_s(vertex)


def edge_curve(edge):
    return BRep_Tool.Curve_s(edge, 0.0, 0.0)


def face_surface(face):
    return BRep_Tool.Surface_s(face)


def face_triangulation(*args):
    return BRep_Tool.Triangulation_s(*args)


__all__ = [
    "BACKEND_NAME",
    "BACKEND_VERSION",
    "Standard_DomainError",
    "Standard_Failure",
    "add_to_bounds",
    "as_compound",
    "as_compsolid",
    "as_edge",
    "as_face",
    "as_shell",
    "as_solid",
    "as_vertex",
    "as_wire",
    "build_curves_3d",
    "confusion",
    "direction_z",
    "edge_curve",
    "face_surface",
    "face_triangulation",
    "first_vertex",
    "last_vertex",
    "make_fill_face",
    "make_sewing",
    "plane_xoy",
    "read_brep",
    "surface_properties",
    "volume_properties",
    "vertex_point",
    "wire_vertices",
    "write_brep",
]
