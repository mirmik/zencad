from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_Sewing
from OCC.Core.ShapeFix import ShapeFix_Shell, ShapeFix_Solid
from OCC.Core.TopoDS import TopoDS_Solid

import zencad.util
from zencad.geom.face import _polygon
from zencad.lazifier import *
from zencad.geom.shape import Shape, nocached_shape_generator, shape_generator


def _polyhedron_shell(pnts, faces_no):
    faces = []

    for nums in faces_no:
        fpnts = []

        for i in nums:
            fpnts.append(pnts[i])

        faces.append(_polygon(fpnts))

    return _make_shell(faces)


@lazy.lazy(cls=shape_generator)
def polyhedron_shell(pnts, faces_no):
    return _polyhedron_shell(pnts, faces_no)


def _fill3d(shp):
    algo = ShapeFix_Solid()
    return Shape(algo.SolidFromShell(shp.Shell()))


@lazy.lazy(cls=shape_generator)
def fill3d(shp):
    return _fill3d(shp)


def _polyhedron(pnts, faces, shell=False):
    shl = _polyhedron_shell(pnts, faces)

    if shell:
        return shl
    else:
        return _fill3d(shl)


@lazy.lazy(cls=shape_generator)
def polyhedron(pnts, faces, shell=False):
    return _polyhedron(pnts, faces, shell)


def _make_shell(vec):
    algo = BRepOffsetAPI_Sewing()
    for a in vec:
        algo.Add(a.Shape())

    algo.Perform()

    if len(vec) > 1:
        fixer = ShapeFix_Shell(algo.SewedShape())
        fixer.Perform()
        return Shape(fixer.Shell())
    else:
        return Shape(algo.SewedShape())


@lazy.lazy(cls=shape_generator)
def make_shell(vec):
    return _make_shell(vec)


@lazy
def convex_hull(pnts, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental=False, qhull_options=None).simplices

    return faces


def _convex_hull_shape(pnts, shell=False, incremental=False, qhull_options=None):
    from scipy.spatial import ConvexHull

    faces = ConvexHull(pnts, incremental, qhull_options).simplices
    m = _polyhedron(pnts, faces, shell=shell)

    return m


@lazy.lazy(cls=shape_generator)
def convex_hull_shape(*args, **kwargs):
    return _convex_hull_shape(*args, **kwargs)
