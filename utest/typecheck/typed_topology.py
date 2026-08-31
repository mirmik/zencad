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
    assert_type(runtime.box(size=(1, 2, 3), center="xz"), typed.Solid)
    assert_type(runtime.cube(1, 2, 3, True), typed.Solid)
    assert_type(runtime.sphere(1, yaw=1, pitch=(-1, 1)), typed.Solid)
    assert_type(runtime.cylinder(1, 2, yaw=1, center=True), typed.Solid)
    assert_type(runtime.cone(2, 1, 3, yaw=1, center=True), typed.Solid)
    assert_type(runtime.torus(4, 1, yaw=1, pitch=(-1, 1)), typed.Solid)
    assert_type(runtime.halfspace(), typed.Solid)
    assert_type(runtime.make_solid(shell), typed.Solid)
    assert_type(runtime.make_solid((shell,)), typed.Solid)
    assert_type(runtime.empty_shape(), typed.Shape)
    assert_type(runtime.nullshape(), typed.Shape)
    assert_type(runtime.union((shape, solid)), typed.Shape)
    assert_type(runtime.union(shape, solid), typed.Shape)
    assert_type(runtime.intersect((shape, solid)), typed.Shape)
    assert_type(runtime.intersection(shape, solid), typed.Shape)
    assert_type(runtime.difference((shape, solid)), typed.Shape)
    assert_type(runtime.section(shape, solid), typed.Shape)
    assert_type(runtime.section(shape, 0), typed.Shape)
    assert_type(runtime.section(shape, runtime.vector3(0, 0, 1)), typed.Shape)
    assert_type(runtime.extrude(face, 2), typed.Shape)
    assert_type(runtime.linear_extrude(face, runtime.vector3(0, 0, 2)), typed.Shape)
    assert_type(face.extrude(2, center=True), typed.Shape)
    assert_type(face.linear_extrude(2), typed.Shape)
    assert_type(runtime.revol(face, 3, 1), typed.Shape)
    assert_type(face.revol(3, 1), typed.Shape)
    assert_type(runtime.loft((edge, wire)), typed.Solid)
    assert_type(runtime.loft((edge, wire), shell=True), typed.Shell)
    assert_type(
        runtime.pipe(wire, edge, trihedron=typed.PipeTrihedron.FRENET),
        typed.Shape,
    )
    assert_type(runtime.pipe_shell((wire,), edge), typed.Solid)
    assert_type(runtime.pipe_shell((wire,), edge, solid=False), typed.Shell)
    assert_type(
        runtime.pipe_shell(
            (wire,),
            edge,
            binormal=runtime.vector3(1, 0, 0),
            transition=typed.PipeTransition.ROUND_CORNER,
        ),
        typed.Solid,
    )
    assert_type(runtime.sweep(wire, edge, frenet=True), typed.Solid)
    assert_type(
        runtime.revol2(face, 3, sections=12, yaw=(0, 1), roll=(0, 2)),
        typed.Solid,
    )
    assert_type(runtime.fillet(solid, 0.1), typed.Shape)
    assert_type(runtime.chamfer(solid, 0.1), typed.Shape)
    assert_type(runtime.fillet2d(face, 0.1), typed.Face)
    assert_type(runtime.restore_shapetype(solid), typed.Solid)
    assert_type(runtime.restore_shapetype(shape), typed.Shape)
    assert_type(shape.restore_shapetype(), typed.Shape)
    mesh = assert_type(runtime.triangulate(shape, 0.1), typed.MeshData)
    assert_type(runtime.triangulate_face(face, 0.1), typed.MeshData)
    assert_type(mesh.get_nodes(), tuple[tuple[float, float, float], ...])
    assert_type(mesh.get_triangles(), tuple[tuple[int, int, int], ...])
    assert_type(
        runtime.get_nodes(mesh), tuple[tuple[float, float, float], ...]
    )
    assert_type(runtime.get_triangles(mesh), tuple[tuple[int, int, int], ...])
    assert_type(runtime.to_brep(shape, "shape.brep"), None)
    assert_type(runtime.from_brep("shape.brep"), typed.Shape)
    assert_type(runtime.to_stl(shape, "shape.stl", 0.1), bool)
    assert_type(runtime.to_svg_string(shape), str)
    assert_type(runtime.to_svg(shape, "shape.svg"), None)
    assert_type(runtime.from_svg_string("<svg/>"), typed.Shape)
    assert_type(runtime.from_svg("shape.svg"), typed.Shape)
    assert_type(runtime.sew((edge, wire)), typed.Wire)
    assert_type(runtime.sew((face, shell)), typed.Shell)
    assert_type(runtime.offset(solid, 0.1), typed.Shape)
    assert_type(solid.offset(0.1), typed.Shape)
    assert_type(runtime.thicksolid(solid, -0.1, (runtime.point3(),)), typed.Solid)
    assert_type(solid.thicksolid(-0.1, (runtime.point3(),)), typed.Solid)
    assert_type(runtime.shapefix_solid(solid), typed.Solid)
    assert_type(solid.shapefix_solid(), typed.Solid)
    assert_type(runtime.unify(solid), typed.Solid)
    assert_type(solid.unify(), typed.Solid)
    query_point = runtime.point3()
    assert_type(runtime.near_vertex(shape, query_point), typed.Vertex)
    assert_type(runtime.near_edge(shape, query_point), typed.Edge)
    assert_type(runtime.near_wire(shape, query_point), typed.Wire)
    assert_type(runtime.near_face(shape, query_point), typed.Face)
    assert_type(runtime.near_shell(shape, query_point), typed.Shell)
    assert_type(runtime.near_solid(shape, query_point), typed.Solid)
    assert_type(runtime.near_compsolid(shape, query_point), typed.CompSolid)
    assert_type(runtime.near_compound(shape, query_point), typed.Compound)
    assert_type(shape.near_vertex(query_point), typed.Vertex)
    projection = assert_type(
        runtime.project(query_point, edge),
        typed.CurveProjection,
    )
    assert_type(runtime.project_point_on_curve(query_point, edge), typed.CurveProjection)
    assert_type(projection.point, typed.Point3)
    assert_type(projection.parameter, typed.Scalar)
    assert_type(projection.distance, typed.Scalar)
    points = (
        runtime.point3(0, 0, 0),
        runtime.point3(1, 0, 0),
        runtime.point3(1, 1, 0),
    )
    assert_type(runtime.circle_arc(*points), typed.Edge)
    assert_type(runtime.make_wire((edge, wire)), typed.Wire)
    assert_type(runtime.rounded_polysegment(points, 0.1), typed.Wire)
    assert_type(runtime.helix(1, 2, step=0.5), typed.Wire)
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
