from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_Sewing
from OCC.Core.ShapeFix import ShapeFix_Shell, ShapeFix_Solid
from OCC.Core.TopoDS import TopoDS_Solid

import zencad.util
from zencad.geom.face import polygon
from zencad.lazifier import *
from zencad.shape import Shape, nocached_shape_generator, shape_generator


@lazy.lazy(cls=nocached_shape_generator)
def make_shell(vec):
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


@lazy.lazy(cls=nocached_shape_generator)
def polyhedron_shell(pnts, faces_no):
    faces = []

    for nums in faces_no:
        fpnts = []

        for i in nums:
            fpnts.append(pnts[i])

        faces.append(polygon(fpnts))

    return make_shell(faces)


@lazy.lazy(cls=nocached_shape_generator)
def fill3d(shp):
    algo = ShapeFix_Solid()
    return Shape(algo.SolidFromShell(shp.Shell()))


@lazy.lazy(cls=nocached_shape_generator)
def polyhedron(pnts, faces, shell=False):
    shl = polyhedron_shell(pnts, faces)

    if shell:
        return shl
    else:
        return fill3d(shl)
