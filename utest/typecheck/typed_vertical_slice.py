"""Static contract for the representative internal typed-domain chain."""

from typing import assert_type

from zencad import _typed as typed


def representative_chain(runtime: typed.Runtime) -> typed.Shape:
    outer = assert_type(runtime.box(10), typed.Shape)
    inner = assert_type(runtime.box(4).translate(3, 3, 3), typed.Shape)
    result = assert_type(outer - inner, typed.Shape)
    faces = assert_type(result.faces(), typed.DeferredSequence[typed.Face])
    face = assert_type(faces[0], typed.Face)
    mass = assert_type(result.mass(), typed.Scalar)
    center = assert_type(result.center(), typed.Point3)
    offset = assert_type(typed.Vector3(mass / 1000, center.y, 0), typed.Vector3)
    moved = assert_type(result.translate(offset), typed.Shape)
    assert_type(face, typed.Face)
    return moved
