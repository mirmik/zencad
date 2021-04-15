import math

import OCC.Core.BRepPrimAPI
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE
from OCC.Core.gp import gp_Circ, gp, gp_Pnt, gp_Pln, gp_Vec, gp_Dir
from OCC.Core.GC import GC_MakeCircle
from OCC.Core.GeomAbs import GeomAbs_C2
from OCC.Core.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCC.Core.ShapeFix import ShapeFix_Face
from OCC.Core.BRepFill import brepfill
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
import OCC.Core.Addons


from zencad.lazifier import lazy
from zencad.geom.shape import Shape, nocached_shape_generator, shape_generator
from zencad.util import as_indexed
import zencad.util
from zencad.util import deg, point3
from zencad.geom.sew import _sew
import zencad.geom.wire as wire
import zencad.geom.face as face
import zencad.geom.wire as wire_module
import zencad.geom.unify as unify
import zencad.geom.operations as operations
import zencad.geom.boolops as boolops
import zencad.geom.curve as curve
from zencad.geom.trans import rotateZ
from zencad.util import vector3, point3, points

from zencad.opencascade_types import *


def _interpolate2(refs, degmin=3, degmax=7):
    Arr = opencascade_array2_of_pnt(refs)
    Surf = GeomAPI_PointsToBSplineSurface(
        Arr, degmin, degmax, GeomAbs_C2, 1.0e-3)
    return Shape(BRepBuilderAPI_MakeFace(Surf.Surface(), 1.0e-5).Face())


# def _fill(shp):
    # return Shape(BRepBuilderAPI_MakeFace(shp.Wire_orEdgeToWire()).Face())

def _fill(wires):
    if not isinstance(wires, (list, tuple)):
        return Shape(BRepBuilderAPI_MakeFace(wires.Wire_orEdgeToWire()).Face())

    algo = BRepBuilderAPI_MakeFace(wires[0].Wire_orEdgeToWire())

    for i in range(1, len(wires)):
        algo.Add(wires[i].Wire_orEdgeToWire())

    algo.Build()

    fixer = ShapeFix_Face(algo.Face())
    fixer.Perform()
    fixer.FixOrientation()
    return Shape(fixer.Face())


def _polygon(pnts, wire=False):
    pnts = points(pnts)

    if wire:
        return wire_module._polysegment(pnts, closed=True)

    mk = BRepBuilderAPI_MakePolygon()

    for i in range(len(pnts)):
        mk.Add(pnts[i].Pnt())

    mk.Close()
    return Shape(BRepBuilderAPI_MakeFace(mk.Shape()).Face())


def _rectangle_wire(a, b, center):
    if center:
        x = a / 2
        y = b / 2
        return wire.polysegment([(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0)], True)
    else:
        return wire.polysegment([(0, 0, 0), (a, 0, 0), (a, b, 0), (0, b, 0)], True)


def _rectangle(a, b=None, center=False, wire=False):
    if b is None:
        b = a

    wr = rectangle_wire(a, b, center)
    if wire:
        return wr
    else:
        return fill(wr)


def _square(*args, **kwargs):
    return rectangle(*args, **kwargs)


def _circle_edge(r, angle=None):
    if angle is None:
        return wire._make_edge(curve._circle(r))

    else:
        angle = zencad.util.angle_pair(angle)
        return wire._make_edge(curve._circle(r), angle)


def _circle(r, angle=None, wire=False):
    if wire is True:
        return _circle_edge(r, angle)

    else:
        if angle is None:
            return _fill(_circle_edge(r))

        else:
            angle = zencad.util.angle_pair(angle)
            a1, a2 = angle[0], angle[1]

            aEdge = _circle_edge(r, angle).Edge()
            aEdge1 = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(
                r * math.cos(a1), r * math.sin(a1), 0)).Edge()
            aEdge2 = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(
                r * math.cos(a2), r * math.sin(a2), 0)).Edge()
            aCircle = BRepBuilderAPI_MakeWire(aEdge, aEdge1, aEdge2).Wire()
            return Shape(BRepBuilderAPI_MakeFace(aCircle).Face())


def _ngon(r, n, wire=False):
    pnts = [0] * n

    for i in range(n):
        angle = 2 * math.pi / n * i
        pnts[i] = point3(r * math.cos(angle), r * math.sin(angle), 0)

    if wire:
        return wire_module.polysegment(pnts, closed=True)
    return polygon(pnts)


def register_font(fontpath):
    OCC.Core.Addons.register_font(fontpath)


def _textshape(text, fontname, size, composite_curve=False):
    aspect = OCC.Core.Addons.Font_FA_Regular
    textshp = OCC.Core.Addons.text_to_brep(text, fontname,
                                           aspect, size, composite_curve)

    return Shape(textshp)


def _ellipse(r1, r2, angle=None, wire=False):
    if r2 > r1:
        inversed_sizes = True
        r1, r2 = r2, r1
    else:
        inversed_sizes = False

    crv = curve._ellipse(r1, r2)

    if angle:
        angle = zencad.util.angle_pair(angle)
        edg = wire_module._make_edge(crv, angle)

        if not wire:
            ret = edg
        else:
            ucrv = crv
            p1 = ucrv._d0(angle[0])
            p2 = ucrv._d0(angle[1])

            wr = _sew([edg,
                       wire_module._segment(p1, (0, 0)),
                       wire_module._segment(p2, (0, 0))])
            ret = _fill(wr)

    else:
        edg = wire_module._make_edge(crv)
        ret = edg if wire else _fill(edg)

    if inversed_sizes:
        return rotateZ(deg(90))(ret)
    else:
        return ret


@lazy.lazy(cls=nocached_shape_generator)
def ellipse(r1, r2, angle=None, wire=False):
    return _ellipse(r1, r2, angle, wire)


@lazy.lazy(cls=nocached_shape_generator)
def fill(shp):
    return _fill(shp)

# @lazy.lazy(cls=nocached_shape_generator)
# def make_face(wires):
#    return _make_face(wires)


@lazy.lazy(cls=nocached_shape_generator)
def ngon(r, n, wire=False):
    return _ngon(r, n, wire)


@lazy.lazy(cls=nocached_shape_generator)
def textshape(text, fontname, size, composite_curve=False):
    return _textshape(text, fontname, size, composite_curve)


@lazy.lazy(cls=nocached_shape_generator)
def circle(r, angle=None, wire=False):
    return _circle(r, angle, wire)


@lazy.lazy(cls=nocached_shape_generator)
def polygon(pnts, wire=False):
    return _polygon(pnts, wire=wire)


@lazy.lazy(cls=nocached_shape_generator)
def rectangle(a, b=None, center=False, wire=False):
    return _rectangle(a, b, center=center, wire=wire)


@lazy.lazy(cls=nocached_shape_generator)
def square(*args, **kwargs):
    return _square(*args, **kwargs)


@lazy.lazy(cls=nocached_shape_generator)
def interpolate2(*args, **kwargs):
    return _interpolate2(*args, **kwargs)


@lazy.lazy(cls=nocached_shape_generator)
def rectangle_wire(a, b, center):
    return _rectangle_wire(a, b, center)


def _wideedge(spine, rad, last_p0, last_p1, circled_joints):
    import zencad.geom.sweep as sweep
    # TODO: переимплементировать без сегмента
    import zencad

    if spine.shapetype() != "edge":
        raise Exception("argument 'curve' should be edge")

    ad0 = spine.endpoints()[0]
    ad1 = spine.endpoints()[1]

    d10 = spine.d1(spine.range()[0]).cross(vector3(0, 0, 1)).normalize()
    d11 = spine.d1(spine.range()[1]).cross(vector3(0, 0, 1)).normalize()

    # начальные точки
    p00 = ad0 + (d10 * rad)
    p01 = ad0 - (d10 * rad)

    # конечные точки
    p10 = ad1 + (d11 * rad)
    p11 = ad1 - (d11 * rad)

    perp = wire_module._segment(p00, p01)
    wc = sweep._pipe(perp, spine, mode="corrected_frenet")

    wc = wc.faces()[0]

    if circled_joints is False:
        if last_p1 is not None and last_p0 is not None:
            wc = wc + face._polygon([last_p0, p00, ad0])
            wc = wc + face._polygon([last_p1, p01, ad0])
    else:
        if last_p1 is not None and last_p0 is not None:
            wc += face._circle(r=rad).mov(vector3(ad0))

    return wc, p10, p11  # union(edgs)


def _widewire(spine, r, circled_joints=True, circled_ends=True):
    edges = spine.edges()
    p0 = None
    p1 = None
    rad = r
    arr = []
    for e in edges:
        f, p0, p1 = _wideedge(e, rad, p0, p1, circled_joints=circled_joints)
        arr.append(f)

    if circled_ends:
        arr.append(face.circle(r=rad).move(spine.endpoints()[0]))
        arr.append(face.circle(r=rad).move(spine.endpoints()[1]))

    return unify._unify(boolops._union(arr))


@lazy.lazy(cls=shape_generator)
def widewire(spine, r, circled_joints=True, circled_ends=True):
    return _widewire(spine, r, circled_joints, circled_ends)


def _fix_face(shp):
    fixer = ShapeFix_Face(shp.Face())
    fixer.Perform()
    fixer.FixOrientation()
    return Shape(fixer.Face())


@lazy.lazy(cls=shape_generator)
def fix_face(shp):
    return _fix_face(shp)


def _infplane():
    aFace = BRepBuilderAPI_MakeFace(
        gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))).Face()
    return Shape(aFace)


@lazy.lazy(cls=shape_generator)
def infplane():
    return _infplane()


def _make_face(surf, u1=None, u2=None, v1=None, v2=None):
    if u1 is None:
        u1, u2, v1, v2 = surf.Surface().Bounds()

    algo = BRepBuilderAPI_MakeFace(surf.Surface(), u1, u2, v1, v2, 1e-6)
    algo.Build()
    return Shape(algo.Face())


def _ruled(a, b):
    return Shape(brepfill.Face(a.Edge(), b.Edge()))


@lazy.lazy(cls=shape_generator)
def ruled(a, b):
    return _ruled(a, b)
