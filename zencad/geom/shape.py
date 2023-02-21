# !/usr/bin/env python3

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Vertex
from OCC.Core.BinTools import BinTools_ShapeSet
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.TopoDS import topods
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.TopExp import topexp, TopExp_Explorer
from OCC.Core.BRepLProp import BRepLProp_SLProps
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepGProp import brepgprop
#from OCC.Core.BRepAdaptor import BRepAdaptor_HCurve
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.GCPnts import GCPnts_UniformAbscissa

from zencad.bbox import BoundaryBox
from zencad.geom.boolops_base import *
from zencad.lazifier import *
import zencad.geom.trans
from zencad.geom.trans import Transformation
from zencad.geom.general_transformation import GeneralTransformation
from OCC.Core.Bnd import Bnd_Box
import zencad.geom.transformable
import binascii
from zencad.util import to_numpy, point3, vector3
from OCC.Core.BRepBndLib import brepbndlib
from zencad.geom.curve_algo import CurveAlgo
from OCC.Core.BinTools import BinTools_ShapeSet, bintools

import io
import base64 as b64
import numpy


class Shape(zencad.geom.transformable.Transformable, CurveAlgo):
    """ Basic zencad type. Является оболочкой для объекта геометрической формы TopoDS_Shape."""

    def __init__(self, arg):
        if not isinstance(arg, TopoDS_Shape):
            raise Exception(
                f"Wrong Shape constructor invoke. Invoked with type: {arg.__class__}")

        self._shp = arg

    def Shape(self): return self._shp
    def Wire(self): return topods.Wire(self._shp)
    def Edge(self): return topods.Edge(self._shp)
    def Face(self): return topods.Face(self._shp)
    def Vertex(self): return topods.Vertex(self._shp)
    def Shell(self): return topods.Shell(self._shp)
    def Solid(self): return topods.Solid(self._shp)
    def Compound(self): return topods.Compound(self._shp)
    def CompSolid(self): return topods.CompSolid(self._shp)

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
        from zencad.geom.sweep import _extrude
        return _extrude(self, vec, center=center)

    def fillet(self, r, refs=None):
        from zencad.geom.operations import _fillet
        return _fillet(self, r, refs=refs)

    def chamfer(self, r, refs=None):
        from zencad.geom.operations import _chamfer
        return _chamfer(self, r, refs=refs)

    def fillet2d(self, r, refs=None):
        from zencad.geom.operations import _fillet2d
        return _fillet2d(self, r, refs=refs)

    def chamfer2d(self, r, refs=None):
        from zencad.geom.operations import _chamfer2d
        return _chamfer2d(self, r, refs=refs)

    def _SLProps(self, u, v):
        prop = BRepLProp_SLProps(self.AdaptorSurface(), u, v, 1, 1e-5)
        return prop

    def normal(self, u=0, v=0):
        from zencad.geom.operations import _restore_shapetype
        shp = _restore_shapetype(self)

        if not shp.is_face():
            raise Exception(
                "Can't take normal from non face shape. type:", self.shapetype())

        return vector3(shp._SLProps(u, v).Normal())

    def __getstate__(self):
        return {"shape": self._shp}

    def __setstate__(self, dct):
        from zencad.geom.offset import _shapefix_solid
        try:
            self._shp = dct["shape"]

            # thicksolid даёт невалидный пиклинг.
            if self.is_solid():
                self._shp = _shapefix_solid(Shape(self._shp)).Shape()
        except Exception as ex:
            print(ex)

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

    def edges(self): return self.reflection_elements(topods.Edge, TopAbs_EDGE)
    def wires(self): return self.reflection_elements(topods.Wire, TopAbs_WIRE)
    def faces(self): return self.reflection_elements(topods.Face, TopAbs_FACE)

    def solids(self): return self.reflection_elements(
        topods.Solid, TopAbs_SOLID)

    def compounds(self): return self.reflection_elements(
        topods.Compound, TopAbs_COMPOUND)

    def shells(self): return self.reflection_elements(
        topods.Shell, TopAbs_SHELL)

    def native_vertices(self): return self.reflection_elements(
        topods.Vertex, TopAbs_VERTEX)

    def vertices(self):
        verts = self.native_vertices()
        pnts = []
        pnts_filtered = []

        for vertex in verts:
            pnt = BRep_Tool.Pnt(vertex.Vertex())
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
        import zencad.geom.face
        assert(self.is_wire_or_edge())
        obj = zencad.geom.face._fill(self)
        return obj

    # def project(self, arg):
    #    import zencad.geom.project
    #    return zencad.geom.project._project(self, arg)

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
        from zencad.geom.curve import Curve
        return Curve(self.Curve()).HCurveAdaptor()

    def Curve(self):
        aCurve = BRep_Tool.Curve(self.Edge())
        return aCurve[0]

    def SurfaceProperties(self):
        props = GProp_GProps()
        brepgprop.SurfaceProperties(self.Shape(), props)
        return props

    def VolumeProperties(self):
        props = GProp_GProps()
        brepgprop.VolumeProperties(self.Shape(), props)
        return props

    def is_volumed(self):
        return len(self.solids()) != 0

    def center(self):
        from zencad.geom.operations import _restore_shapetype

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
        brepbndlib.Add(self.Shape(), box)
        xl, yl, zl, xh, yh, zh = box.Get()
        return BoundaryBox(xl, xh, yl, yh, zl, zh)


# Support lazy methods


class LazyObjectShape(evalcache.LazyObject):
    """ Lazy object wrapper for Shape class.
            It control methods lazyfying. And add some checks.
            All Shapes wrappers must use LazyShapeObject. 
    """

    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def unlazy(self):
        """Test wrapped object type equality."""
        obj = super().unlazy()
        if not isinstance(obj, Shape):
            raise Exception(
                f"LazyObjectShape wraped type is not Shape: class:{obj.__class__}")
        return obj

    def _generic(name, cached, cls, prevent=None):
        def foo(self, *args, **kwargs):
            return self.lazyinvoke(
                getattr(Shape, name),
                (self, *args),
                kwargs,
                cached=cached,
                cls=cls,
                prevent=prevent
            )

        return foo

    def _generic_unlazy(name):
        def foo(self, *args, **kwargs):
            return getattr(Shape, name)(self.unlazy(), *args, **kwargs)
        return foo

    nolazy_methods = [
        "Shape", "Vertex", "Wire", "Edge", "Solid", "Face",
        "Compound", "Shell", "CompSolid", "Wire_orEdgeToWire",
        "reflection_elements", "AdaptorSurface", "AdaptorCurve", "HCurveAdaptor",
        "_SLProps", "VolumeProperties", "Curve", "SurfaceProperties"
    ]

    transparent_methods = [
    ]

    cached_methods = [
        "__add__", "__sub__", "__xor__",
        "scaleX", "scaleY", "scaleZ", "scaleXYZ",
        "extrude", "chamfer", "fillet", "chamfer2d", "fillet2d", "fill", "trimmed_edge"
    ]

    nocached_methods = [
        "up", "down", "left", "right", "forw", "back",
        "move", "moveX", "moveY", "moveZ",
        "mov", "movX", "movY", "movZ",
        "translate", "translateX", "translateY", "translateZ",
        "rotate", "rotateX", "rotateY", "rotateZ",
        "rot", "rotX", "rotY", "rotZ",
        "mirror", "mirrorX", "mirrorY", "mirrorZ",
        "mirrorYZ", "mirrorXY", "mirrorXZ",
        "scale", "transform",
        "shapetype"

        #"props1", "props2", "props3"
    ]

    # Методы, которые возвращают не shape
    standart_methods = [
        "is_wire", "is_compsolid", "is_edge", "is_compound", "is_vertex",
        "is_face", "is_shell", "is_wire_or_edge", "is_solid", "is_volumed",
        "is_closed",
        "edges", "wires", "faces", "vertices", "native_vertices",
        "shells", "solids", "compounds", "bbox", "boundbox",
        "value", "d0", "d1", "normal", "range", "endpoints", "center", "uniform", "uniform_points",
        "mass", "curvetype", 'ellipse_parameters', 'line_parameters', 'circle_parameters', 'lower_distance_parameter'
    ]


for item in LazyObjectShape.nocached_methods:
    setattr(LazyObjectShape, item, LazyObjectShape._generic(
        item, False, cls=LazyObjectShape))

for item in LazyObjectShape.nolazy_methods:
    setattr(LazyObjectShape, item, LazyObjectShape._generic_unlazy(item))

for item in LazyObjectShape.standart_methods:
    setattr(LazyObjectShape, item, LazyObjectShape._generic(
        item, False, cls=evalcache.LazyObject))

for item in LazyObjectShape.cached_methods:
    setattr(LazyObjectShape, item, LazyObjectShape._generic(
        item, True, cls=LazyObjectShape))

for item in LazyObjectShape.transparent_methods:
    setattr(LazyObjectShape, item, LazyObjectShape._generic(
            item, False, cls=LazyObjectShape, prevent=["self"]))


class nocached_shape_generator(evalcache.LazyObject):
    """ Decorator for heavy functions.
            It use caching for lazy data restoring."""

    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.lazyinvoke(
            self, args, kwargs, encache=False, decache=False, cls=LazyObjectShape
        )


class shape_generator(evalcache.LazyObject):
    """ Decorator for lightweight functions.
            It prevent caching."""

    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.lazyinvoke(self, args, kwargs, cls=LazyObjectShape)


A = (
    set(Shape.__dict__.keys()).union(
        set(zencad.geom.transformable.Transformable.__dict__.keys()),
        set(CurveAlgo.__dict__.keys())
    )
)

B = set(LazyObjectShape.__dict__.keys())

C = B.difference(A).difference({
    "transparent_methods", "cached_methods", "standart_methods", "nocached_methods", "unlazy", "_generic", "_generic_unlazy", "nolazy_methods"
})

D = A.difference(B).difference({
    "__dict__", "__weakref__", "__getstate__", "__setstate__"
})

if len(D) != 0:
    print("Warning: LazyShapeObject has not wrappers for methods:")
    print(D)

if len(C) != 0:
    print(
        "Warning: LazyShapeObject has wrappers for unexisted methods:")
    print(C)
