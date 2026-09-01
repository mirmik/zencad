"""Static contracts for shell, polyhedron, hull, and platonic factories."""

from typing_extensions import assert_type

from zencad import geom as typed


def shell_constructor_contract(context: typed.Context, dynamic: bool) -> None:
    points = (
        context.call(typed.point3, 0, 0, 0),
        context.call(typed.point3, 1, 0, 0),
        context.call(typed.point3, 0, 1, 0),
        context.call(typed.point3, 0, 0, 1),
    )
    faces = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))
    face = context.call(typed.polygon, (points[0], points[1], points[2]))
    shell = assert_type(context.call(typed.make_shell, face), typed.Shell)
    assert_type(context.call(typed.fill3d, shell), typed.Solid)
    assert_type(context.call(typed.polyhedron_shell, points, faces), typed.Shell)
    assert_type(context.call(typed.polyhedron, points, faces), typed.Solid)
    assert_type(context.call(typed.polyhedron, points, faces, True), typed.Shell)
    assert_type(
        context.call(typed.polyhedron, points, faces, dynamic),
        typed.Solid | typed.Shell,
    )
    assert_type(context.call(typed.convex_hull, points), tuple[tuple[int, ...], ...])
    assert_type(context.call(typed.convex_hull_shape, points), typed.Solid)
    assert_type(context.call(typed.convex_hull_shape, points, shell=True), typed.Shell)
    assert_type(
        context.call(typed.convex_hull_shape, points, dynamic),
        typed.Solid | typed.Shell,
    )
    assert_type(
        context.call(
            typed.tetrahedron,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.tetrahedron, shell=True), typed.Shell)
    assert_type(
        context.call(
            typed.hexahedron,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.hexahedron, 1, None, True), typed.Shell)
    assert_type(
        context.call(
            typed.octahedron,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.octahedron, shell=True), typed.Shell)
    assert_type(
        context.call(
            typed.dodecahedron,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.dodecahedron, shell=True), typed.Shell)
    assert_type(
        context.call(
            typed.icosahedron,
        ),
        typed.Solid,
    )
    assert_type(context.call(typed.icosahedron, shell=True), typed.Shell)
    assert_type(context.call(typed.platonic, 4), typed.Solid)
    assert_type(context.call(typed.platonic, 20, shell=True), typed.Shell)
    assert_type(
        context.call(typed.platonic, 6, 1, None, dynamic), typed.Solid | typed.Shell
    )
    module_shell = assert_type(typed.make_shell(face), typed.Shell)
    assert_type(typed.fill3d(module_shell), typed.Solid)
    assert_type(typed.polyhedron_shell(points, faces), typed.Shell)
    assert_type(typed.polyhedron(points, faces), typed.Solid)
    assert_type(typed.polyhedron(points, faces, True), typed.Shell)
    assert_type(typed.polyhedron(points, faces, dynamic), typed.Solid | typed.Shell)
    assert_type(typed.convex_hull(points), tuple[tuple[int, ...], ...])
    assert_type(typed.convex_hull_shape(points), typed.Solid)
    assert_type(typed.convex_hull_shape(points, shell=True), typed.Shell)
    assert_type(typed.convex_hull_shape(points, dynamic), typed.Solid | typed.Shell)
    assert_type(typed.tetrahedron(), typed.Solid)
    assert_type(typed.tetrahedron(shell=True), typed.Shell)
    assert_type(typed.hexahedron(), typed.Solid)
    assert_type(typed.hexahedron(1, None, True), typed.Shell)
    assert_type(typed.octahedron(), typed.Solid)
    assert_type(typed.octahedron(shell=True), typed.Shell)
    assert_type(typed.dodecahedron(), typed.Solid)
    assert_type(typed.dodecahedron(shell=True), typed.Shell)
    assert_type(typed.icosahedron(), typed.Solid)
    assert_type(typed.icosahedron(shell=True), typed.Shell)
    assert_type(typed.platonic(4), typed.Solid)
    assert_type(typed.platonic(20, shell=True), typed.Shell)
    assert_type(typed.platonic(6, 1, None, dynamic), typed.Solid | typed.Shell)
