from zencad.shape import Shape, shape_generator
from zencad.lazifier import *
from zencad.util import vector3
from zencad.geom.trans import translate

from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_COMPOUND, TopAbs_COMPSOLID, TopAbs_SHELL, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir

from OCC.Core.GeomFill import GeomFill_IsFixed, GeomFill_IsFrenet, GeomFill_IsDarboux, GeomFill_IsDiscreteTrihedron, GeomFill_IsCorrectedFrenet, GeomFill_IsConstantNormal, GeomFill_IsCorrectedFrenet, GeomFill_IsGuideAC, GeomFill_IsGuidePlan, GeomFill_IsGuideACWithContact, GeomFill_IsGuidePlanWithContact
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe, BRepOffsetAPI_MakePipeShell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transformed

from zencad.util import *
from zencad.geom.operations import _restore_shapetype


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

    except:
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


# Труба вытягивает круглый профиль по заданному контуру.
# def _tube_section(shp, radius, tol, cont, maxdegree, maxsegm):
# {
#    auto crv = servoce::circle_curve3(radius).rotZ(M_PI/2);
#    auto slaw = servoce::law_evolved_section(crv, servoce::law_constant_function(1, crv.range()));
#    auto llaw = servoce::law_spine_and_trihedron(shp, law_corrected_frenet_trihedron());
#
#    auto surf = servoce::sweep_surface(slaw, llaw, tol, cont, maxdegree, maxsegm);
#    auto strt_crv = surf.v_iso_curve(surf.vrange().first);
#    auto fini_crv = surf.v_iso_curve(surf.vrange().second);
#
#    //throw std::runtime_error("HERE2");
#    auto sedge = make_edge(strt_crv);
#    auto fedge = make_edge(fini_crv);
#    auto face = make_face(surf);
#
#    return std::make_tuple(face, sedge, fedge);
# }
#
# // Труба по wire состоит из нескольких труб по edge
# std::tuple<shell_shape, edge_shape, edge_shape> servoce::make_tube(
#    const servoce::wire_shape& shp, double radius, double tol, int cont, int maxdegree, int maxsegm
#    )
# {
#    std::vector<face_shape> faces;
#    std::vector<edge_shape> strt;
#    std::vector<edge_shape> fini;
#
#    for ( auto& e : shp.edges() )
#    {
#        auto tpl = make_tube(e, radius, tol, cont, maxdegree, maxsegm);
#
#        faces.push_back(std::get<0>(tpl));
#        strt.push_back(std::get<1>(tpl));
#        fini.push_back(std::get<2>(tpl));
#    }
#
#    return std::make_tuple(make_shell(faces), strt[0], fini[fini.size()-1]);
# }
