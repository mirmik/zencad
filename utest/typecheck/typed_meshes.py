"""Static contract for typed indexed mesh extraction."""

from typing_extensions import assert_type

from zencad import geom as typed


def mesh_contract(
    context: typed.Context,
    shape: typed.Shape,
    face: typed.Face,
    mesh: typed.MeshData,
) -> None:
    assert_type(shape.to_mesh(), typed.MeshData)
    assert_type(shape.to_mesh(0.2, 0.4), typed.MeshData)
    assert_type(face.triangulate(), typed.MeshData)
    assert_type(typed.to_mesh(shape), typed.MeshData)
    assert_type(typed.triangulate(face), typed.MeshData)
    assert_type(mesh.value(), typed.MeshDataRecord)
    assert_type(mesh.positions, tuple[tuple[float, float, float], ...])
    assert_type(mesh.normals, tuple[tuple[float, float, float], ...])
    assert_type(mesh.triangles, tuple[tuple[int, int, int], ...])
    assert_type(mesh.triangle_face_ids, tuple[int, ...])
    assert_type(mesh.vertex_count, int)
    assert_type(mesh.triangle_count, int)
    assert_type(mesh.dropped_triangles, int)
    assert_type(mesh.boundbox(), typed.BoundaryBox)
    assert_type(typed.mesh_boundbox(mesh), typed.BoundaryBox)
    assert_type(typed.get_nodes(mesh), tuple[tuple[float, float, float], ...])
    assert_type(typed.get_triangles(mesh), tuple[tuple[int, int, int], ...])
    assert_type(mesh.display_payload(), bytes)
    assert_type(typed.mesh_display_payload(mesh), bytes)
    record = mesh.value()
    assert_type(record.vertex_count, int)
    assert_type(record.triangle_count, int)

    assert_type(
        typed.MeshData.from_data(
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            ((0.0, 0.0, 1.0),) * 3,
            ((0, 1, 2),),
            (0,),
            context=context,
        ),
        typed.MeshData,
    )
