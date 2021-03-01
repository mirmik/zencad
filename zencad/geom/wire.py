from zencad.shape import Shape, nocached_shape_generator, shape_generator
from zencad.util import as_indexed
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

from OCC.Core.GCE2d import GCE2d_MakeSegment
from OCC.Core.Geom2d import Geom2d_Line, Geom2d_TrimmedCurve
from OCC.Core.Geom import Geom_CylindricalSurface, Geom_ConicalSurface
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Ax2d, gp_Ax3, gp_DZ, gp_Pnt2d, gp_Dir2d
from OCC.Core.GeomAPI import GeomAPI_Interpolate
from OCC.Core.TColgp import TColgp_HArray1OfPnt, TColgp_Array1OfVec
from OCC.Core.TColStd import TColStd_HArray1OfBoolean
from OCC.Core.GC import GC_MakeArcOfCircle
from OCC.Core.Precision import precision_Confusion
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Wire
from OCC.Core.BRepLib import breplib

from zencad.lazifier import *
from zencad.geom.sew import sew
from zencad.util import points, to_Pnt, to_Vec
from zencad.geom.project import project
import zencad.geom.curve as curve

from zencad.util import *

import math
import numpy


def _make_edge(crv, interval=None) -> Shape:
    aCurve = crv.Curve()
    if interval is None:
        return Shape(BRepBuilderAPI_MakeEdge(aCurve).Edge())
    else:
        return Shape(BRepBuilderAPI_MakeEdge(aCurve, interval[0], interval[1]).Edge())


@lazy.lazy(cls=nocached_shape_generator)
def make_edge(crv, interval=None) -> Shape:
    return _make_edge(crv, interval)


def _circle_arc(p1, p2, p3):
    aArcOfCircle = GC_MakeArcOfCircle(to_Pnt(p1), to_Pnt(p2), to_Pnt(p3))
    return Shape(BRepBuilderAPI_MakeEdge(aArcOfCircle.Value()).Edge())


@lazy.lazy(cls=nocached_shape_generator)
def circle_arc(p1, p2, p3):
    return _circle_arc(p1, p2, p3)


def _polysegment(pnts, closed=False) -> Shape:
    if len(pnts) <= 1:
        raise Exception("Need at least two points for polysegment")

    mkWire = BRepBuilderAPI_MakeWire()

    for i in range(len(pnts)-1):
        mkWire.Add(BRepBuilderAPI_MakeEdge(
            to_Pnt(pnts[i]), to_Pnt(pnts[i + 1])).Edge())

    if (closed):
        mkWire.Add(BRepBuilderAPI_MakeEdge(
            to_Pnt(pnts[len(pnts) - 1]), to_Pnt(pnts[0])).Edge())

    return Shape(mkWire.Wire())


@lazy.lazy(cls=nocached_shape_generator)
def polysegment(pnts, closed=False):
    return _polysegment(pnts, closed)


def _segment(a, b) -> Shape:
    a, b = points((a, b))
    return Shape(BRepBuilderAPI_MakeEdge(to_Pnt(a), to_Pnt(b)).Edge())


@lazy.lazy(cls=nocached_shape_generator)
def segment(a, b) -> Shape:
    return _segment(a, b)


def _interpolate(pnts, tang=None, closed=False):
    return _make_edge(
        curve._interpolate(pnts=pnts, tang=tang, closed=closed))


@lazy.lazy(cls=shape_generator)
def interpolate(*args, **kwargs):
    return _interpolate(*args, **kwargs)


def _bezier(pnts, weights=None):
    return _make_edge(curve._bezier(pnts, weights))


@lazy.lazy(cls=nocached_shape_generator)
def bezier(pnts, weights=None):
    return _bezier(pnts, weights)


def _bspline(
        poles,
        knots,
        muls,
        degree: int,
        periodic: bool = False,
        weights=None,
        check_rational: bool = None
):
    return make_edge(curve.bspline(
        poles=poles,
        knots=knots,
        muls=muls,
        degree=degree,
        periodic=periodic,
        weights=weights,
        check_rational=check_rational))


@lazy.lazy(cls=nocached_shape_generator)
def bspline(*args, **kwargs):
    return _bspline(*args, **kwargs)


def _rounded_polysegment(pnts, r, closed=False):
    # Для того, чтобы закрыть контур, не теряя скругления, перекрёстно добавляем две точки,
    # Две в начале, другую в конце.
    pnts = points(pnts)
    if closed:
        pnts.insert(0, pnts[-1])
        pnts.append(pnts[1])

    cpnts = pnts[1:-1]

    pairs = []
    pairs_tang = []
    pairs.append((None, pnts[0]))

    for i in range(len(cpnts)):
        a = segment(pnts[i], pnts[i+1]).unlazy()
        b = segment(pnts[i+1], pnts[i+2]).unlazy()

        ad1 = a.d1(a.range()[1])
        bd1 = b.d1(b.range()[0])

        n = numpy.cross(bd1, ad1)

        if numpy.linalg.norm(n) == 0:
            pairs.append((cpnts[i], cpnts[i]))
            pairs_tang.append(None)
            continue

        abn = numpy.cross(ad1, n)
        bbn = numpy.cross(bd1, n)

        temp = (abn + bbn)
        bn = temp/numpy.linalg.norm(temp) * r

        c = cpnts[i] + bn

        ca = project(c, a)
        cb = project(c, b)

        pairs.append((ca, cb))
        pairs_tang.append((ad1, bd1))

    pairs.append((pnts[-1], None))

    nodes = []
    for i in range(len(cpnts)):
        nodes.append(segment(pairs[i][1], pairs[i+1][0]))
        if pairs_tang[i] is not None:
            nodes.append(interpolate(
                pnts=[pairs[i+1][0], pairs[i+1][1]], tang=[pairs_tang[i][0], pairs_tang[i][1]]))
    nodes.append(segment(pairs[-2][1], pairs[-1][0]))

    # Для замыкания необходимо удалить крайние сегменты.
    if closed:
        del nodes[0]
        del nodes[-1]

    result = sew(nodes)

    # И, наконец, зашиваем прореху.
    if closed:
        result = sew([
            result,
            segment(result.endpoints()[0], result.endpoints()[1])
        ])

    return result


@lazy.lazy(cls=shape_generator)
def rounded_polysegment(*args, **kwargs):
    return _rounded_polysegment(*args, **kwargs)

# ***********
# makeLongHelix is a workaround for an OCC problem found in helices with more than
# some magic number of turns.  See Mantis #0954. (FreeCad)
# ***********


def _helix(r, h, step=None, pitch=None, angle=0, left=False):
    radius = r
    height = h

    if pitch:
        pitch = math.sin(pitch) * 2 * math.pi*r
    else:
        pitch = step

    if pitch < precision_Confusion():
        raise Exception("Pitch of helix too small")

    if height < precision_Confusion():
        raise Exception("Height of helix too small")

    cylAx2 = gp_Ax2(gp_Pnt(0.0, 0.0, 0.0), gp_DZ())

    if abs(angle) < precision_Confusion():
        # Cylindrical helix
        if radius < precision_Confusion():
            raise Exception("Radius of helix too small")

        surf = Geom_CylindricalSurface(gp_Ax3(cylAx2), radius)
        isCylinder = True
    else:
        # Conical helix
        if abs(angle) < precision_Confusion():
            raise Exception("Angle of helix too small")

        surf = Geom_ConicalSurface(gp_Ax3(cylAx2), angle, radius)
        isCylinder = False

    turns = height / pitch
    wholeTurns = math.floor(turns)
    partTurn = turns - wholeTurns

    aPnt = gp_Pnt2d(0, 0)
    aDir = gp_Dir2d(2. * math.pi, pitch)
    coneDir = 1.0

    if left:
        aDir.SetCoord(-2. * math.pi, pitch)
        coneDir = -1.0

    aAx2d = gp_Ax2d(aPnt, aDir)
    line = Geom2d_Line(aAx2d)
    beg = line.Value(0)

    mkWire = BRepBuilderAPI_MakeWire()

    for i in range(wholeTurns):
        if isCylinder:
            end = line.Value(
                math.sqrt(4.0 * math.pi * math.pi + pitch * pitch) * (i + 1))
        else:
            u = coneDir * (i + 1) * 2.0 * math.pi
            v = ((i + 1) * pitch) / math.cos(angle)
            end = gp_Pnt2d(u, v)

        segm = GCE2d_MakeSegment(beg, end).Value()
        edgeOnSurf = BRepBuilderAPI_MakeEdge(segm, surf).Edge()
        mkWire.Add(edgeOnSurf)
        beg = end

    if partTurn > precision_Confusion():
        if (isCylinder):
            end = line.Value(
                math.sqrt(4.0 * math.pi * math.pi + pitch * pitch) * turns)
        else:
            u = coneDir * turns * 2.0 * math.pi
            v = height / math.cos(angle)
            end = gp_Pnt2d(u, v)

        segm = GCE2d_MakeSegment(beg, end).Value()
        edgeOnSurf = BRepBuilderAPI_MakeEdge(segm, surf).Edge()
        mkWire.Add(edgeOnSurf)

    shape = mkWire.Wire()
    breplib.BuildCurves3d(shape)
    return Shape(shape)


@lazy.lazy(cls=shape_generator)
def helix(*args, **kwargs):
    return _helix(*args, **kwargs)
