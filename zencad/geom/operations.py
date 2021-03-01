from zencad.lazifier import *
from zencad.shape import Shape, nocached_shape_generator, shape_generator

from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeFillet2d

from zencad.geom.near import _near_vertex
from zencad.util import *


def _restore_shapetype(shp):
    if len(shp.solids()) == 1:
        return shp.solids()[0]

    if len(shp.shells()) == 1:
        return shp.shells()[0]

    elif len(shp.faces()) == 1:
        return shp.faces()[0]

    elif len(shp.wires()) == 1:
        return shp.wires()[0]

    elif len(shp.edges()) == 1:
        return shp.edges()[0]

    return shp


@lazy.lazy(cls=shape_generator)
def restore_shapetype(shp):
    return _restore_shapetype(shp)


def _fillet(shp, r, refs=None):
    if refs:
        refs = points(refs)

    if shp.is_solid() or shp.is_compound() or shp.is_compsolid():
        mk = BRepFilletAPI_MakeFillet(shp.Shape())

        if refs:
            for p in refs:
                minimum = float("inf")
                vtx = p.Vtx()

                for edg in shp.edges():
                    extrema = BRepExtrema_DistShapeShape(edg.Edge(), vtx)

                    if minimum > extrema.Value():
                        ret = edg
                        minimum = extrema.Value()

                mk.Add(r, ret.Edge())
        else:
            for edg in shp.edges():
                mk.Add(r, edg.Edge())

        return Shape(mk.Shape())
    else:
        raise Exception("Fillet argument has unsuported type.")


def _chamfer(shp, r, refs=None):
    if refs:
        refs = points(refs)

    if shp.is_solid() or shp.is_compound() or shp.is_compsolid():
        mk = BRepFilletAPI_MakeChamfer(shp.Shape())

        if refs:
            for p in refs:
                minimum = float("inf")
                vtx = p.Vtx()

                for edg in shp.edges():
                    extrema = BRepExtrema_DistShapeShape(edg.Edge(), vtx)

                    if minimum > extrema.Value():
                        ret = edg
                        minimum = extrema.Value()

                mk.Add(r, ret.Edge())
        else:
            for edg in shp.edges():
                mk.Add(r, edg.Edge())

        return Shape(mk.Shape())
    else:
        raise Exception("Fillet argument has unsuported type.")


@lazy.lazy(cls=shape_generator)
def chamfer(shp, r, refs=None):
    return _chamfer(shp, r, refs)


@lazy.lazy(cls=shape_generator)
def fillet(shp, r, refs=None):
    return _fillet(shp, r, refs)


def _fillet2d(shp, r, refs=None):
    mk = BRepFilletAPI_MakeFillet2d(shp.Face())

    if refs is None:
        refs = shp.vertices()

    for p in refs:
        mk.AddFillet(_near_vertex(shp, p).Vertex(), r)

    return Shape(mk.Shape())


@lazy.lazy(cls=shape_generator)
def fillet2d(shp, r, refs=None):
    return _fillet2d(shp, r, refs)
