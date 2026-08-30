"""Static contract for precise typed topology handles."""

from collections.abc import Iterator

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
    assert_type(shape.shapetype(), typed.ShapeKind)
    assert_type(shape.is_vertex(), bool)
    assert_type(shape.is_edge(), bool)
    assert_type(shape.is_wire(), bool)
    assert_type(shape.is_face(), bool)
    assert_type(shape.is_shell(), bool)
    assert_type(shape.is_solid(), bool)
    assert_type(shape.is_compsolid(), bool)
    assert_type(shape.is_compound(), bool)
    assert_type(shape.is_wire_or_edge(), bool)
    assert_type(shape.is_closed(), bool)
    assert_type(shape.is_volumed(), bool)
    assert_type(shape.Wire_orEdgeToWire(), typed.Wire)
    assert_type(edge.to_wire(), typed.Wire)
    assert_type(edge.curvetype(), typed.CurveKind)
    assert_type(edge.d0(0), typed.Point3)
    assert_type(edge.d1(0), typed.Vector3)
    assert_type(edge.range(), typed.Interval)
    assert_type(edge.endpoints(), tuple[typed.Point3, typed.Point3])
    assert_type(edge.line_parameters(), typed.LineParameters)
    assert_type(edge.lower_distance_parameter(runtime.point3()), typed.Scalar)
    assert_type(edge.trimmed_edge(0, 1), typed.Edge)
    assert_type(edge.uniform(3), list[typed.Scalar])
    assert_type(edge.uniform_points(3), list[typed.Point3])
    assert_type(face.surface(), typed.Surface)
    assert_type(face.normal(), typed.Vector3)
    surface_properties = assert_type(face.SurfaceProperties(), typed.ShapeProperties)
    volume_properties = assert_type(solid.VolumeProperties(), typed.ShapeProperties)
    assert_type(surface_properties.center, typed.Point3)
    assert_type(surface_properties.mass, typed.Scalar)
    assert_type(volume_properties.center, typed.Point3)
    assert_type(volume_properties.mass, typed.Scalar)
    assert_type(wire.fill(), typed.Face)
    assert_type(face.extrude(runtime.vector3(0, 0, 1)), typed.Shape)
    assert_type(face.extrude(1, True), typed.Shape)
    assert_type(solid.fillet(0.1), typed.Shape)
    assert_type(solid.chamfer(0.1, (runtime.point3(),)), typed.Shape)
    assert_type(face.fillet2d(0.1), typed.Face)
    assert_type(face.chamfer2d(0.1), typed.Face)
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

    vertices = assert_type(shape.vertices(), typed.DeferredSequence[typed.Vertex])
    assert_type(shape.native_vertices(), typed.DeferredSequence[typed.Vertex])
    edges = assert_type(shape.edges(), typed.DeferredSequence[typed.Edge])
    wires = assert_type(shape.wires(), typed.DeferredSequence[typed.Wire])
    faces = assert_type(shape.faces(), typed.DeferredSequence[typed.Face])
    shells = assert_type(shape.shells(), typed.DeferredSequence[typed.Shell])
    solids = assert_type(shape.solids(), typed.DeferredSequence[typed.Solid])
    compounds = assert_type(shape.compounds(), typed.DeferredSequence[typed.Compound])
    compsolids = assert_type(
        shape.compsolids(), typed.DeferredSequence[typed.CompSolid]
    )

    assert_type(vertices[0], typed.Vertex)
    assert_type(vertices[-1], typed.Vertex)
    assert_type(edges[0], typed.Edge)
    assert_type(wires[0], typed.Wire)
    assert_type(faces[0], typed.Face)
    assert_type(shells[0], typed.Shell)
    assert_type(solids[0], typed.Solid)
    assert_type(compounds[0], typed.Compound)
    assert_type(compsolids[0], typed.CompSolid)

    assert_type(iter(vertices), Iterator[typed.Vertex])
    assert_type(len(vertices), int)

    # Boolean topology is not stable, even when both inputs are solids.
    assert_type(solid - solid, typed.Shape)
