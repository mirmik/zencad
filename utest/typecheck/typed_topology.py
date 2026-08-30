"""Static contract for precise typed topology handles."""

from typing_extensions import assert_type

from zencad import _typed as typed


def topology_contract(
    runtime: typed.Runtime,
    shape: typed.Shape,
    vertex: typed.Vertex,
    edge: typed.Edge,
    wire: typed.Wire,
    face: typed.Face,
    shell: typed.Shell,
    solid: typed.Solid,
    compound: typed.Compound,
    compsolid: typed.CompSolid,
) -> None:
    transform = runtime.translation(1, 2, 3)

    assert_type(runtime.box(1), typed.Solid)
    assert_type(runtime.box(1).translate(1, 2, 3), typed.Solid)
    assert_type(runtime.box(1).transform(transform), typed.Solid)

    assert_type(shape.translate(1, 2, 3), typed.Shape)
    assert_type(shape.transform(transform), typed.Shape)
    assert_type(vertex.translate(1, 2, 3), typed.Vertex)
    assert_type(vertex.transform(transform), typed.Vertex)
    assert_type(edge.translate(1, 2, 3), typed.Edge)
    assert_type(edge.transform(transform), typed.Edge)
    assert_type(wire.translate(1, 2, 3), typed.Wire)
    assert_type(wire.transform(transform), typed.Wire)
    assert_type(face.translate(1, 2, 3), typed.Face)
    assert_type(face.transform(transform), typed.Face)
    assert_type(shell.translate(1, 2, 3), typed.Shell)
    assert_type(shell.transform(transform), typed.Shell)
    assert_type(solid.translate(1, 2, 3), typed.Solid)
    assert_type(solid.transform(transform), typed.Solid)
    assert_type(compound.translate(1, 2, 3), typed.Compound)
    assert_type(compound.transform(transform), typed.Compound)
    assert_type(compsolid.translate(1, 2, 3), typed.CompSolid)
    assert_type(compsolid.transform(transform), typed.CompSolid)

    assert_type(vertex.point(), typed.Point3)
    assert_type(shape.faces(), typed.DeferredSequence[typed.Face])
    assert_type(shape.faces()[0], typed.Face)

    # Boolean topology is not stable, even when both inputs are solids.
    assert_type(solid - solid, typed.Shape)
