# !/usr/bin/env python3

from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform
from OCP.TopoDS import TopoDS_Shape, TopoDS_Vertex
from OCP.BinTools import BinTools_ShapeSet
from OCP.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.gp import gp_Pnt, gp_Vec
from OCP.TopExp import TopExp_Explorer
from OCP.BRepLProp import BRepLProp_SLProps
from OCP.GProp import GProp_GProps
#from OCP.BRepAdaptor import BRepAdaptor_HCurve
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformAbscissa

from zencad.bbox import BoundaryBox
from zencad._native.boolops_base import *
import zencad._native.trans
from zencad._native.trans import Transformation
from zencad._native.general_transformation import GeneralTransformation
from OCP.Bnd import Bnd_Box
import zencad._native.transformable
import binascii
from zencad.util import to_numpy, point3, vector3
from zencad._native.curve_algo import CurveAlgo
from zencad.occ_compat import (
    add_to_bounds,
    as_compound,
    as_compsolid,
    as_edge,
    as_face,
    as_shell,
    as_solid,
    as_vertex,
    as_wire,
    edge_curve,
    read_brep,
    surface_properties,
    vertex_point,
    volume_properties,
    write_brep,
)

import io
import base64 as b64
import numpy


class Shape(zencad._native.transformable.Transformable, CurveAlgo):
    """ Basic zencad type. Является оболочкой для объекта геометрической формы TopoDS_Shape."""

    def __init__(self, arg):
        if not isinstance(arg, TopoDS_Shape):
            raise Exception(
                f"Wrong Shape constructor invoke. Invoked with type: {arg.__class__}")

        self._shp = arg

    def Shape(self): return self._shp
    def Wire(self): return as_wire(self._shp)
    def Edge(self): return as_edge(self._shp)
    def Face(self): return as_face(self._shp)
    def Vertex(self): return as_vertex(self._shp)
    def Shell(self): return as_shell(self._shp)
    def Solid(self): return as_solid(self._shp)
    def Compound(self): return as_compound(self._shp)
    def CompSolid(self): return as_compsolid(self._shp)

    def Wire_orEdgeToWire(self):
        if (self.Shape().ShapeType() == TopAbs_WIRE):
            return self.Wire()
        else:
            return BRepBuilderAPI_MakeWire(self.Edge()).Wire()

    def __add__(self, oth):
        return Shape(occ_pair_union(self._shp, oth._shp))

    def __sub__(self, oth):
        return Shape(occ_pair_difference(self._shp, oth._shp))

    def __xor__(self, oth):
        return Shape(occ_pair_intersect(self._shp, oth._shp))

    def extrude(self, vec, center=False):
        from zencad._native.sweep import _extrude
        return _extrude(self, vec, center=center)

    def fillet(self, r, refs=None):
        from zencad._native.operations import _fillet
        return _fillet(self, r, refs=refs)

    def chamfer(self, r, refs=None):
        from zencad._native.operations import _chamfer
        return _chamfer(self, r, refs=refs)

    def validate(self, *, exact=False, parallel=False):
        from zencad._native.validation import validate
        return validate(self, exact=exact, parallel=parallel)

    def is_valid(self, *, exact=False, parallel=False):
        from zencad._native.validation import is_valid
        return is_valid(self, exact=exact, parallel=parallel)

    def assert_valid(self, *, exact=False, parallel=False):
        from zencad._native.validation import assert_valid
        return assert_valid(self, exact=exact, parallel=parallel)

    def clean(self):
        from zencad._native.validation import _clean
        return _clean(self)

    def heal(self, tolerance=1e-7, max_tolerance=1e-3):
        from zencad._native.validation import _heal
        return _heal(self, tolerance, max_tolerance)

    def fillet2d(self, r, refs=None):
        from zencad._native.operations import _fillet2d
        return _fillet2d(self, r, refs=refs)

    def chamfer2d(self, r, refs=None):
        from zencad._native.operations import _chamfer2d
        return _chamfer2d(self, r, refs=refs)

    def _SLProps(self, u, v):
        prop = BRepLProp_SLProps(self.AdaptorSurface(), u, v, 1, 1e-5)
        return prop

    def normal(self, u=0, v=0):
        from zencad._native.operations import _restore_shapetype
        shp = _restore_shapetype(self)

        if not shp.is_face():
            raise Exception(
                "Can't take normal from non face shape. type:", self.shapetype())

        return vector3(shp._SLProps(u, v).Normal())

    def __getstate__(self):
        stream = io.BytesIO()
        write_brep(self._shp, stream)
        return {"brep": stream.getvalue()}

    def __setstate__(self, dct):
        from zencad._native.offset import _shapefix_solid
        if "brep" in dct:
            self._shp = TopoDS_Shape()
            read_brep(self._shp, io.BytesIO(dct["brep"]))
            if self._shp.IsNull():
                raise ValueError("Failed to restore cached BREP shape")
        else:
            # Compatibility with in-memory state produced by pythonocc. An
            # incompatible backend object must fail unpickling so evalcache
            # can discard and recompute the entry instead of retaining a
            # half-initialized Shape.
            self._shp = dct["shape"]

        if not isinstance(self._shp, TopoDS_Shape):
            raise TypeError("Cached shape belongs to an incompatible backend")

        # thicksolid даёт невалидный пиклинг.
        if self.is_solid():
            self._shp = _shapefix_solid(Shape(self._shp)).Shape()

    def transform(self, trans):
        if isinstance(trans, Transformation):
            shp = BRepBuilderAPI_Transform(
                self._shp, trans._trsf, True).Shape()
            return Shape(shp)

        if isinstance(trans, GeneralTransformation):
            shp = BRepBuilderAPI_GTransform(
                self._shp, trans._gtrsf, True).Shape()
            return Shape(shp)

    def is_wire(self): return self.Shape().ShapeType() == TopAbs_WIRE
    def is_edge(self): return self.Shape().ShapeType() == TopAbs_EDGE
    def is_face(self): return self.Shape().ShapeType() == TopAbs_FACE
    def is_solid(self): return self.Shape().ShapeType() == TopAbs_SOLID
    def is_compound(self): return self.Shape().ShapeType() == TopAbs_COMPOUND
    def is_compsolid(self): return self.Shape().ShapeType() == TopAbs_COMPSOLID
    def is_shell(self): return self.Shape().ShapeType() == TopAbs_SHELL
    def is_vertex(self): return self.Shape().ShapeType() == TopAbs_VERTEX
    def is_wire_or_edge(self): return self.is_edge() or self.is_wire()

    def is_closed(self):
        if not self.is_wire_or_edge():
            raise Exception("Only for wire or edge")

        strt, fini = self.endpoints()
        return numpy.linalg.norm(fini-strt) < 1e-4

    def shapetype(self):
        if self.Shape().ShapeType() == TopAbs_VERTEX:
            return "vertex"
        elif self.Shape().ShapeType() == TopAbs_WIRE:
            return "wire"
        elif self.Shape().ShapeType() == TopAbs_EDGE:
            return "edge"
        elif self.Shape().ShapeType() == TopAbs_FACE:
            return "face"
        elif self.Shape().ShapeType() == TopAbs_SOLID:
            return "solid"
        elif self.Shape().ShapeType() == TopAbs_SHELL:
            return "shell"
        elif self.Shape().ShapeType() == TopAbs_COMPSOLID:
            return "compsolid"
        elif self.Shape().ShapeType() == TopAbs_COMPOUND:
            return "compound"

    def reflection_elements(self, getter, topabs):
        ret = []
        ex = TopExp_Explorer(self.Shape(), topabs)
        while ex.More():
            obj = getter(ex.Current())
            ret.append(Shape(obj))
            ex.Next()
        return ret

    def edges(self): return self.reflection_elements(as_edge, TopAbs_EDGE)
    def wires(self): return self.reflection_elements(as_wire, TopAbs_WIRE)
    def faces(self): return self.reflection_elements(as_face, TopAbs_FACE)

    def solids(self): return self.reflection_elements(
        as_solid, TopAbs_SOLID)

    def compounds(self): return self.reflection_elements(
        as_compound, TopAbs_COMPOUND)

    def shells(self): return self.reflection_elements(
        as_shell, TopAbs_SHELL)

    def native_vertices(self): return self.reflection_elements(
        as_vertex, TopAbs_VERTEX)

    def vertices(self):
        verts = self.native_vertices()
        pnts = []
        pnts_filtered = []

        for vertex in verts:
            pnt = vertex_point(vertex.Vertex())
            pnts.append(point3(pnt))

        # Фильтруем вершины, исключая близколежащие.
        for p in pnts:
            for f in pnts_filtered:
                if numpy.linalg.norm(p-f) < 1e-5:
                    break
            else:
                pnts_filtered.append(p)

        return pnts_filtered

    def fill(self):
        import zencad._native.face
        assert(self.is_wire_or_edge())
        obj = zencad._native.face._fill(self)
        return obj

    def to_mesh(self, *args, **kwargs):
        """Triangulate this shape into display-ready indexed mesh data."""
        from zencad._native.mesh import to_mesh

        return to_mesh(self, *args, **kwargs)

    # def project(self, arg):
    #    import zencad._native.project
    #    return zencad._native.project._project(self, arg)

    # TODO: Вынести в surface_algo
    def AdaptorSurface(self):
        assert(self.is_face())
        return BRepAdaptor_Surface(self.Face())

    # TODO: Вынести в curve_algo
    def AdaptorCurve(self):
        assert(self.is_edge())
        return BRepAdaptor_Curve(self.Edge())

    def HCurveAdaptor(self):
        assert(self.is_edge())
        from zencad._native.curve import Curve
        return Curve(self.Curve()).HCurveAdaptor()

    def Curve(self):
        return edge_curve(self.Edge())

    def SurfaceProperties(self):
        props = GProp_GProps()
        surface_properties(self.Shape(), props)
        return props

    def VolumeProperties(self):
        props = GProp_GProps()
        volume_properties(self.Shape(), props)
        return props

    def is_volumed(self):
        return len(self.solids()) != 0

    def center(self):
        from zencad._native.operations import _restore_shapetype

        if not self.is_volumed():
            centerMass = self.SurfaceProperties().CentreOfMass()
            return point3(centerMass)

        centerMass = self.VolumeProperties().CentreOfMass()
        return point3(centerMass)

    def mass(self):
        return self.VolumeProperties().Mass()

    def uniform(self, npoints, strt=None, fini=None):
        if strt is None and fini is None:
            strt, fini = self.range()

        ret = []
        adaptor = self.AdaptorCurve()
        algo = GCPnts_UniformAbscissa(adaptor, npoints, strt, fini)

        for i in range(npoints):
            ret.append(algo.Parameter(i + 1))

        return ret

    def uniform_points(self, npoints, strt=None, fini=None):
        params = self.uniform(npoints, strt, fini)
        return [self.d0(p) for p in params]

    def bbox(self):
        return self.boundbox()

    def boundbox(self):
        box = Bnd_Box()
        add_to_bounds(self.Shape(), box)
        xl, yl, zl, xh, yh, zh = box.Get()
        return BoundaryBox(xl, xh, yl, yh, zl, zh)


class shape_generator:
    """Deprecated decorator marker retained for eager backend imports."""


class nocached_shape_generator(shape_generator):
    """Deprecated decorator marker retained for eager backend imports."""
