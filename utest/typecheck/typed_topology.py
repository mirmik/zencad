"""Static contract for precise typed topology handles."""

from collections.abc import Iterator

from typing_extensions import assert_type

from zencad import geom as typed


def topology_contract(
    context: typed.Context,
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
    transform = context.call(typed.translation, 1, 2, 3)

    assert_type(context.call(typed.box, 1), typed.Solid)
    assert_type(context.call(typed.box, size=(1, 2, 3), center="xz"), typed.Solid)
    assert_type(context.call(typed.cube, 1, 2, 3, True), typed.Solid)
    assert_type(context.call(typed.sphere, 1, yaw=1, pitch=(-1, 1)), typed.Solid)
    assert_type(context.call(typed.cylinder, 1, 2, yaw=1, center=True), typed.Solid)
    assert_type(context.call(typed.cone, 2, 1, 3, yaw=1, center=True), typed.Solid)
    assert_type(context.call(typed.torus, 4, 1, yaw=1, pitch=(-1, 1)), typed.Solid)
    assert_type(
        context.call(
            typed.halfspace,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.make_solid, shell), typed.Solid)
    assert_type(context.call(typed.make_solid, (shell,)), typed.Solid)
    assert_type(
        context.call(
            typed.empty_shape,
        ),
        typed.Shape,
    )
    assert_type(
        context.call(
            typed.nullshape,
        ),
        typed.Shape,
    )
    assert_type(context.call(typed.union, (shape, solid)), typed.Shape)
    assert_type(context.call(typed.union, shape, solid), typed.Shape)
    assert_type(context.call(typed.intersect, (shape, solid)), typed.Shape)
    assert_type(context.call(typed.intersection, shape, solid), typed.Shape)
    assert_type(context.call(typed.difference, (shape, solid)), typed.Shape)
    assert_type(context.call(typed.section, shape, solid), typed.Shape)
    assert_type(context.call(typed.section, shape, 0), typed.Shape)
    assert_type(
        context.call(typed.section, shape, context.call(typed.vector3, 0, 0, 1)),
        typed.Shape,
    )
    assert_type(typed.empty_shape(), typed.Shape)
    assert_type(typed.nullshape(), typed.Shape)
    assert_type(typed.union((shape, solid)), typed.Shape)
    assert_type(typed.union(shape, solid), typed.Shape)
    assert_type(typed.intersect((shape, solid)), typed.Shape)
    assert_type(typed.intersection(shape, solid), typed.Shape)
    assert_type(typed.difference((shape, solid)), typed.Shape)
    assert_type(typed.section(shape, solid), typed.Shape)
    assert_type(typed.section(shape, 0), typed.Shape)
    assert_type(context.call(typed.extrude, face, 2), typed.Shape)
    assert_type(
        context.call(typed.linear_extrude, face, context.call(typed.vector3, 0, 0, 2)),
        typed.Shape,
    )
    assert_type(face.extrude(2, center=True), typed.Shape)
    assert_type(face.linear_extrude(2), typed.Shape)
    assert_type(context.call(typed.revol, face, 3, 1), typed.Shape)
    assert_type(face.revol(3, 1), typed.Shape)
    assert_type(typed.extrude(face, 2), typed.Shape)
    assert_type(typed.linear_extrude(face, 2), typed.Shape)
    assert_type(typed.revol(face, 3, 1), typed.Shape)
    assert_type(context.call(typed.loft, (edge, wire)), typed.Solid)
    assert_type(context.call(typed.loft, (edge, wire), shell=True), typed.Shell)
    assert_type(typed.loft((edge, wire)), typed.Solid)
    assert_type(typed.loft((edge, wire), shell=True), typed.Shell)
    assert_type(
        context.call(typed.pipe, wire, edge, trihedron=typed.PipeTrihedron.FRENET),
        typed.Shape,
    )
    assert_type(context.call(typed.pipe_shell, (wire,), edge), typed.Solid)
    assert_type(context.call(typed.pipe_shell, (wire,), edge, solid=False), typed.Shell)
    assert_type(typed.pipe(wire, edge), typed.Shape)
    assert_type(typed.pipe_shell((wire,), edge), typed.Solid)
    assert_type(typed.pipe_shell((wire,), edge, solid=False), typed.Shell)
    assert_type(
        context.call(
            typed.pipe_shell,
            (wire,),
            edge,
            binormal=context.call(typed.vector3, 1, 0, 0),
            transition=typed.PipeTransition.ROUND_CORNER,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.sweep, wire, edge, frenet=True), typed.Solid)
    assert_type(typed.sweep(wire, edge, frenet=True), typed.Solid)
    assert_type(
        context.call(typed.revol2, face, 3, sections=12, yaw=(0, 1), roll=(0, 2)),
        typed.Solid,
    )
    assert_type(
        typed.revol2(face, 3, sections=12, yaw=(0, 1), roll=(0, 2)),
        typed.Solid,
    )
    assert_type(context.call(typed.fillet, solid, 0.1), typed.Shape)
    assert_type(context.call(typed.chamfer, solid, 0.1), typed.Shape)
    assert_type(context.call(typed.fillet2d, face, 0.1), typed.Face)
    assert_type(typed.fillet(solid, 0.1), typed.Shape)
    assert_type(typed.chamfer(solid, 0.1), typed.Shape)
    assert_type(typed.fillet2d(face, 0.1), typed.Face)
    assert_type(typed.chamfer2d(face, 0.1), typed.Face)
    assert_type(context.call(typed.restore_shapetype, solid), typed.Solid)
    assert_type(context.call(typed.restore_shapetype, shape), typed.Shape)
    assert_type(shape.restore_shapetype(), typed.Shape)
    mesh = assert_type(context.call(typed.to_mesh, shape, 0.1), typed.MeshData)
    assert_type(context.call(typed.triangulate, face, 0.1), typed.MeshData)
    assert_type(mesh.get_nodes(), tuple[tuple[float, float, float], ...])
    assert_type(mesh.get_triangles(), tuple[tuple[int, int, int], ...])
    assert_type(
        typed.get_nodes(mesh), tuple[tuple[float, float, float], ...]
    )
    assert_type(
        typed.get_triangles(mesh), tuple[tuple[int, int, int], ...]
    )
    assert_type(context.call(typed.to_brep, shape, "shape.brep"), None)
    assert_type(context.call(typed.from_brep, "shape.brep"), typed.Shape)
    assert_type(context.call(typed.to_stl, shape, "shape.stl", 0.1), bool)
    assert_type(context.call(typed.export_stl, shape, "shape.stl"), None)
    assert_type(context.call(typed.export_step, shape, "shape.step"), None)
    assert_type(context.call(typed.export_3mf, shape, "shape.3mf"), None)
    assert_type(context.call(typed.to_svg_string, shape), str)
    assert_type(context.call(typed.to_svg, shape, "shape.svg"), None)
    assert_type(context.call(typed.from_svg_string, "<svg/>"), typed.Shape)
    assert_type(context.call(typed.from_svg, "shape.svg"), typed.Shape)
    assert_type(typed.to_brep(shape, "shape.brep"), None)
    assert_type(typed.from_brep("shape.brep"), typed.Shape)
    assert_type(typed.to_stl(shape, "shape.stl", 0.1), bool)
    assert_type(typed.export_stl(shape, "shape.stl"), None)
    assert_type(typed.export_step(shape, "shape.step"), None)
    assert_type(typed.export_3mf(shape, "shape.3mf"), None)
    assert_type(typed.to_svg_string(shape), str)
    assert_type(typed.to_svg(shape, "shape.svg"), None)
    assert_type(typed.from_svg_string("<svg/>"), typed.Shape)
    assert_type(typed.from_svg("shape.svg"), typed.Shape)
    assert_type(context.call(typed.sew, (edge, wire)), typed.Wire)
    assert_type(context.call(typed.sew, (face, shell)), typed.Shell)
    assert_type(typed.sew((edge, wire)), typed.Wire)
    assert_type(typed.sew((face, shell)), typed.Shell)
    assert_type(context.call(typed.offset, solid, 0.1), typed.Shape)
    assert_type(solid.offset(0.1), typed.Shape)
    assert_type(typed.offset(solid, 0.1), typed.Shape)
    assert_type(
        context.call(
            typed.thicksolid,
            solid,
            -0.1,
            (
                context.call(
                    typed.point3,
                ),
            ),
        ),
        typed.Solid,
    )
    assert_type(
        solid.thicksolid(
            -0.1,
            (
                context.call(
                    typed.point3,
                ),
            ),
        ),
        typed.Solid,
    )
    assert_type(
        typed.thicksolid(
            solid,
            -0.1,
            (
                context.call(
                    typed.point3,
                ),
            ),
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.shapefix_solid, solid), typed.Solid)
    assert_type(solid.shapefix_solid(), typed.Solid)
    assert_type(typed.shapefix_solid(solid), typed.Solid)
    assert_type(context.call(typed.unify, solid), typed.Solid)
    assert_type(typed.unify(solid), typed.Solid)
    assert_type(context.call(typed.validate, solid), typed.ValidationReport)
    assert_type(typed.validate(solid), typed.ValidationReport)
    assert_type(solid.validate(), typed.ValidationReport)
    assert_type(context.call(typed.is_valid, solid), bool)
    assert_type(typed.is_valid(solid), bool)
    assert_type(solid.is_valid(), bool)
    assert_type(context.call(typed.assert_valid, solid), typed.Solid)
    assert_type(typed.assert_valid(solid), typed.Solid)
    assert_type(solid.assert_valid(), typed.Solid)
    assert_type(context.call(typed.clean, solid), typed.Solid)
    assert_type(typed.clean(solid), typed.Solid)
    assert_type(solid.clean(), typed.Solid)
    assert_type(context.call(typed.heal, solid), typed.Solid)
    assert_type(typed.heal(solid), typed.Solid)
    assert_type(solid.heal(), typed.Solid)
    assert_type(typed.restore_shapetype(shape), typed.Shape)
    assert_type(
        typed.near_vertex(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Vertex,
    )
    assert_type(
        typed.near_edge(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Edge,
    )
    assert_type(
        typed.near_wire(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Wire,
    )
    assert_type(
        typed.near_face(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Face,
    )
    assert_type(
        typed.near_shell(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Shell,
    )
    assert_type(
        typed.near_solid(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Solid,
    )
    assert_type(
        typed.near_compsolid(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.CompSolid,
    )
    assert_type(
        typed.near_compound(
            shape,
            context.call(
                typed.point3,
            ),
        ),
        typed.Compound,
    )
    assert_type(
        typed.project(
            context.call(
                typed.point3,
            ),
            edge,
        ),
        typed.CurveProjection,
    )
    assert_type(solid.unify(), typed.Solid)
    query_point = context.call(
        typed.point3,
    )
    assert_type(context.call(typed.near_vertex, shape, query_point), typed.Vertex)
    assert_type(context.call(typed.near_edge, shape, query_point), typed.Edge)
    assert_type(context.call(typed.near_wire, shape, query_point), typed.Wire)
    assert_type(context.call(typed.near_face, shape, query_point), typed.Face)
    assert_type(context.call(typed.near_shell, shape, query_point), typed.Shell)
    assert_type(context.call(typed.near_solid, shape, query_point), typed.Solid)
    assert_type(context.call(typed.near_compsolid, shape, query_point), typed.CompSolid)
    assert_type(context.call(typed.near_compound, shape, query_point), typed.Compound)
    assert_type(shape.near_vertex(query_point), typed.Vertex)
    projection = assert_type(
        context.call(typed.project, query_point, edge),
        typed.CurveProjection,
    )
    assert_type(
        context.call(typed.project_point_on_curve, query_point, edge),
        typed.CurveProjection,
    )
    assert_type(projection.point, typed.Point3)
    assert_type(projection.parameter, typed.Scalar)
    assert_type(projection.distance, typed.Scalar)
    points = (
        context.call(typed.point3, 0, 0, 0),
        context.call(typed.point3, 1, 0, 0),
        context.call(typed.point3, 1, 1, 0),
    )
    assert_type(context.call(typed.circle_arc, *points), typed.Edge)
    assert_type(context.call(typed.make_wire, (edge, wire)), typed.Wire)
    assert_type(context.call(typed.rounded_polysegment, points, 0.1), typed.Wire)
    assert_type(context.call(typed.helix, 1, 2, step=0.5), typed.Wire)
    assert_type(context.call(typed.box, 1).translate(1, 2, 3), typed.Solid)
    assert_type(context.call(typed.box, 1).transform(transform), typed.Solid)

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
    assert_type(
        edge.lower_distance_parameter(
            context.call(
                typed.point3,
            )
        ),
        typed.Scalar,
    )
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
    assert_type(face.extrude(context.call(typed.vector3, 0, 0, 1)), typed.Shape)
    assert_type(face.extrude(1, True), typed.Shape)
    assert_type(solid.fillet(0.1), typed.Shape)
    assert_type(
        solid.chamfer(
            0.1,
            (
                context.call(
                    typed.point3,
                ),
            ),
        ),
        typed.Shape,
    )
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

    vertices = assert_type(shape.vertices(), typed.ShapeList[typed.Vertex])
    assert_type(shape.native_vertices(), typed.DeferredSequence[typed.Vertex])
    edges = assert_type(shape.edges(), typed.ShapeList[typed.Edge])
    wires = assert_type(shape.wires(), typed.ShapeList[typed.Wire])
    faces = assert_type(shape.faces(), typed.ShapeList[typed.Face])
    shells = assert_type(shape.shells(), typed.ShapeList[typed.Shell])
    solids = assert_type(shape.solids(), typed.ShapeList[typed.Solid])
    compounds = assert_type(shape.compounds(), typed.ShapeList[typed.Compound])
    compsolids = assert_type(shape.compsolids(), typed.ShapeList[typed.CompSolid])

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
    assert_type(edges[:2], typed.ShapeList[typed.Edge])
    assert_type(edges.filter_by(typed.Axis.Z), typed.ShapeList[typed.Edge])
    assert_type(edges.longer_than(1), typed.ShapeList[typed.Edge])
    assert_type(faces.planar(), typed.ShapeList[typed.Face])
    assert_type(faces.normal_to(typed.Axis.Z), typed.ShapeList[typed.Face])
    assert_type(
        faces.filter_by_position(typed.Axis.Z, 1),
        typed.ShapeList[typed.Face],
    )
    assert_type(faces.filter_by(typed.Plane.XY), typed.ShapeList[typed.Face])
    assert_type(faces.sort_by(typed.Axis.Z), typed.ShapeList[typed.Face])
    assert_type(faces.sort_by_distance((0, 0, 0)), typed.ShapeList[typed.Face])
    assert_type(faces.largest(), typed.Face)
    assert_type(faces.only(), typed.Face)
    assert_type(faces.geometry_types(), tuple[typed.GeomType, ...])
    assert_type(
        faces.group_by(typed.GeomType),
        dict[typed.GeomType, typed.ShapeList[typed.Face]],
    )
    assert_type(typed.fillet(solid, 0.1, edges), typed.Shape)
    assert_type(typed.chamfer(solid, 0.1, edges), typed.Shape)

    # Boolean topology is not stable, even when both inputs are solids.
    assert_type(solid - solid, typed.Shape)
