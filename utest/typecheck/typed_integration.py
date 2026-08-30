"""Static contract for the complete remaining-geometry domain chain."""

from typing_extensions import assert_type

from zencad import _typed as typed


def complete_domain_chain(runtime: typed.Runtime) -> None:
    seed = assert_type(runtime.box(2), typed.Solid)
    shape = assert_type(seed.translate(seed.mass() / 8, 2, 3), typed.Solid)
    edge = assert_type(shape.edges()[0], typed.Edge)
    face = assert_type(shape.faces()[0], typed.Face)
    curve = assert_type(edge.curve(), typed.Curve)
    surface = assert_type(face.surface(), typed.Surface)
    bounds = assert_type(shape.boundbox(), typed.BoundaryBox)
    mesh = assert_type(shape.to_mesh(), typed.MeshData)

    assert_type(curve.range(), typed.Interval)
    assert_type(surface.u_range(), typed.Interval)
    assert_type(surface.v_range(), typed.Interval)
    assert_type(bounds.value(), typed.BoundaryBoxRecord)
    assert_type(mesh.boundbox(), typed.BoundaryBox)
    assert_type(mesh.value(), typed.MeshDataRecord)
