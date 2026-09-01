from zencad.occ_compat import as_shell, make_sewing
from OCP.ShapeFix import ShapeFix_Shell, ShapeFix_Solid
from OCP.TopoDS import TopoDS_Solid, TopoDS_Shell
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeShell

import zencad.util
from zencad._native.face import _polygon
from zencad._eager import eager
from zencad._native.shape import Shape, nocached_shape_generator, shape_generator


def _polyhedron_shell(pnts, faces_no):
    faces = []

    for nums in faces_no:
        fpnts = []

        for i in nums:
            fpnts.append(pnts[i])

        faces.append(_polygon(fpnts))

    return _make_shell(faces)


@eager.decorator(cls=shape_generator)
def polyhedron_shell(pnts, faces_no):
    return _polyhedron_shell(pnts, faces_no)


def _fill3d(shp):
    algo = ShapeFix_Solid()
    return Shape(algo.SolidFromShell(shp.Shell()))


@eager.decorator(cls=shape_generator)
def fill3d(shp):
    return _fill3d(shp)


def _polyhedron(pnts, faces, shell=False):
    shl = _polyhedron_shell(pnts, faces)

    if shell:
        return shl
    else:
        return _fill3d(shl)


@eager.decorator(cls=shape_generator)
def polyhedron(pnts, faces, shell=False):
    return _polyhedron(pnts, faces, shell)


def _make_shell(vec):
    #builder = BRep_Builder()
    #shell = TopoDS_Shell()
    #make_shell = builder.MakeShell(shell)
    #for a in vec:
    #    builder.Add(shell, a.Shape())
    #return Shape(shell)

    algo = make_sewing()
    for a in vec:
        algo.Add(a.Shape())

    algo.Perform()

    if len(vec) > 1:
        fixer = ShapeFix_Shell(as_shell(algo.SewedShape()))
        fixer.Perform()
        return Shape(fixer.Shell())
    else:
        return Shape(algo.SewedShape())


@eager.decorator(cls=shape_generator)
def make_shell(vec):
    return _make_shell(vec)


@eager
def convex_hull(pnts, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental=False, qhull_options=None).simplices

    return faces


def _convex_hull_shape(pnts, shell=False, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental, qhull_options).simplices
    m = _polyhedron(pnts, faces, shell=shell)

    return m


@eager.decorator(cls=shape_generator)
def convex_hull_shape(*args, **kwargs):
    return _convex_hull_shape(*args, **kwargs)
