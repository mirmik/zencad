from zencad.geom.shape import Shape, shape_generator
from zencad.lazifier import lazy
from zencad.util import vector3
from zencad.geom.trans import translate
import zencad.geom.exttrans

from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir, gp_Ax2

from OCC.Core.GeomFill import GeomFill_IsFixed, GeomFill_IsFrenet, GeomFill_IsDarboux, GeomFill_IsDiscreteTrihedron, GeomFill_IsConstantNormal, GeomFill_IsCorrectedFrenet, GeomFill_IsGuideAC, GeomFill_IsGuidePlan, GeomFill_IsGuideACWithContact, GeomFill_IsGuidePlanWithContact
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe, BRepOffsetAPI_MakePipeShell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transformed, BRepBuilderAPI_RoundCorner, BRepBuilderAPI_RightCorner

from zencad.util import deg
from zencad.geom.operations import _restore_shapetype

import zencad.geom.face as face
import zencad.geom.curve as curve
from zencad.geom.sweep_law import law_evolved_section, law_constant_function, law_spine_and_trihedron, law_corrected_frenet_trihedron

from zencad.geom.surface import _sweep_surface
from zencad.geom.wire import _make_edge
from zencad.geom.face import _make_face
from zencad.geom.shell import _make_shell

import math


def _extrude(shp, vec, center=False):
    if type(vec) in (float, int):
        vec = vector3(0, 0, vec)
    else:
        vec = vector3(vec)

    if center:
        trs = translate(-vec / 2)
        return _extrude(trs(shp), vec)

    # Если в объекте есть только один face, но сам объект не face,
    # извлекаем face и применяем влгоритм на нём.
    shp = _restore_shapetype(shp)
    obj = shp.Shape()

    return Shape(BRepPrimAPI_MakePrism(obj, vec.Vec()).Shape())


@lazy.lazy(cls=shape_generator)
def extrude(*args, **kwargs): return _extrude(*args, **kwargs)


def linear_extrude(shp, vec, center=False):
    return extrude(shp, vec, center)


def _revol(shp, r=None, yaw=0.0):
    if r is not None:
        shp = shp.rotX(deg(90)).movX(r)

    ax = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))

    if yaw == 0:
        return Shape(BRepPrimAPI_MakeRevol(shp.Shape(), ax).Shape())
    else:
        return Shape(BRepPrimAPI_MakeRevol(shp.Shape(), ax, yaw).Shape())


@lazy.lazy(cls=shape_generator)
def revol(*args, **kwargs): return _revol(*args, **kwargs)


def _revol2(profile, r, n=30, yaw=(0, deg(360)), roll=(0, 0), sects=False, nparts=None):
    rets = []
    arrs = []

    is_full_circle = abs((yaw[1]-yaw[0]) - deg(360)) < 0.000001

    if is_full_circle:
        endpoint = False
        if nparts is None:
            nparts = 2

    else:
        endpoint = True
        if nparts is None:
            nparts = 1

    def part_of_interval(part, total, a, b):
        def koeff(idx, tot): return idx / tot
        def point(a, b, k): return a*(1-k) + b*k

        return(point(a, b, koeff(part, total)), point(a, b, koeff(part+1, total)))

    for ipart in range(nparts):
        part_n = n // nparts
        part_yaw = part_of_interval(ipart, nparts, yaw[0], yaw[1])
        part_roll = part_of_interval(ipart, nparts, roll[0], roll[1])

        for w in profile.wires():
            m = zencad.geom.exttrans.rotate_array2(
                r=r,
                n=part_n,
                yaw=part_yaw,
                roll=part_roll,
                endpoint=endpoint,
                array=True)(w)

            arrs.append(m)

        # Радиус окружности не имеет значения.
            rets.append(
                _pipe_shell(
                    m,
                    spine=face._circle(r=100, angle=part_yaw, wire=True),
                    # force_approx_c1=True,
                    frenet=True))

        if sects:
            return arrs

    return zencad.geom.boolops._union(rets)


@lazy.lazy(cls=shape_generator)
def revol2(*args, **kwargs):
    return _revol2(*args, **kwargs)


def _loft(arr, smooth=False, shell=False, maxdegree=4):
    builder = BRepOffsetAPI_ThruSections(not shell, not smooth)
    builder.SetMaxDegree(maxdegree)

    for v in arr:
        if v.Shape().ShapeType() == TopAbs_FACE:
            raise Exception("Loft argument must be array of Wires or Edges")

    for r in arr:
        builder.AddWire(r.Wire_orEdgeToWire())

    return Shape(builder.Shape())


@lazy.lazy(cls=shape_generator)
def loft(*args, **kwargs):
    return _loft(*args, **kwargs)


geomfill_triedron_map = {
    "corrected_frenet": GeomFill_IsCorrectedFrenet,
    "fixed": GeomFill_IsFixed,
    "frenet": GeomFill_IsFrenet,
    "constant_normal": GeomFill_IsConstantNormal,
    "darboux": GeomFill_IsDarboux,
    "guide_ac": GeomFill_IsGuideAC,
    "guide_plan": GeomFill_IsGuidePlan,
    "guide_ac_with_contact": GeomFill_IsGuideACWithContact,
    "guide_plan_with_contact": GeomFill_IsGuidePlanWithContact,
    "discrete_trihedron": GeomFill_IsDiscreteTrihedron
}


def _pipe(shp, spine, mode="corrected_frenet", force_approx_c1=False):
    if (spine.Shape().IsNull()):
        raise Exception("Cannot sweep along empty spine")

    if (shp.Shape().IsNull()):
        raise Exception("Cannot sweep empty profile")

    try:
        if isinstance(mode, str):
            tri = geomfill_triedron_map[mode]
        else:
            tri = mode

    except Exception:
        raise Exception("pipe: undefined mode")

    return Shape(BRepOffsetAPI_MakePipe(spine.Wire_orEdgeToWire(), shp.Shape(), tri, force_approx_c1).Shape())


@lazy.lazy(cls=shape_generator)
def pipe(*args, **kwargs):
    return _pipe(*args, **kwargs)


def _pipe_shell(
    arr,
    spine,
    frenet=False,
    approx_c1=False,
    binormal=None,
    parallel=None,
    discrete=False,
    solid=True,
    transition=0
):
    mkPipeShell = BRepOffsetAPI_MakePipeShell(spine.Wire_orEdgeToWire())

    if transition == 1:
        transMode = BRepBuilderAPI_RightCorner
    elif transition == 2:
        transMode = BRepBuilderAPI_RoundCorner
    else:
        transMode = BRepBuilderAPI_Transformed

    mkPipeShell.SetMode(frenet)
    mkPipeShell.SetTransitionMode(transMode)
    mkPipeShell.SetForceApproxC1(approx_c1)

    if binormal is not None:
        mkPipeShell.SetMode(binormal.Dir())

    if parallel is not None:
        mkPipeShell.SetMode(gp_Ax2(gp_Pnt(0, 0, 0), parallel.Dir()))

    if discrete:
        mkPipeShell.SetDiscreteMode()

    for a in arr:
        mkPipeShell.Add(a.Wire_orEdgeToWire())

    if not mkPipeShell.IsReady():
        raise Exception("shape is not ready to build")

    mkPipeShell.Build()

    if solid:
        mkPipeShell.MakeSolid()

    return Shape(mkPipeShell.Shape())


@lazy.lazy(cls=shape_generator)
def pipe_shell(*args, **kwargs):
    return _pipe_shell(*args, **kwargs)


def _tube_section(shp, radius, tol, cont, maxdegree, maxsegm):
    """Труба вытягивает круглый профиль по заданному контуру."""
    crv = curve._circle(radius).rotZ(math.pi/2)
    slaw = law_evolved_section(crv, law_constant_function(1, crv.range()))
    llaw = law_spine_and_trihedron(shp, law_corrected_frenet_trihedron())

    surf = _sweep_surface(slaw, llaw, tol, cont, maxdegree, maxsegm)
    strt_crv = surf.v_iso_curve(surf.vrange()[0])
    fini_crv = surf.v_iso_curve(surf.vrange()[1])

    sedge = _make_edge(strt_crv)
    fedge = _make_edge(fini_crv)
    face = _make_face(surf)

    return face, sedge, fedge


def _tube(spine, r, tol=1e-6, cont=2, maxdegree=3, maxsegm=20, bounds=False):
    """Труба по wire состоит из нескольких труб по edge"""
    faces = []
    strt = []
    fini = []

    for e in spine.edges():
        tpl = _tube_section(e, r, tol, cont, maxdegree, maxsegm)

        faces.append(tpl[0])
        strt.append(tpl[1])
        fini.append(tpl[2])

    if bounds:
        return _make_shell(faces), strt[0], fini[len(fini)-1]
    else:
        return _make_shell(faces)


@lazy.lazy(cls=shape_generator)
def tube(*args, **kwargs):
    return _tube(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def sweep(proto, path, frenet=False):
    """sweep operation is deprecated. use pipe_shell instead"""
    return _pipe_shell([proto], path, frenet)
