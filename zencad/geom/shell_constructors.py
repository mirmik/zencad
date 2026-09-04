"""Typed shell, polyhedron, hull, and platonic constructors."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import math
from numbers import Integral
from typing import Literal, overload

from evalcache import ResultSpec

from zencad._native.shape import Shape as ResolvedShape
from zencad.operation import (
    operation,
    resolve_context,
    using_context,
)

from . import _operations as ops
from .topology import (
    SHELL_SPEC,
    SOLID_SPEC,
    Face,
    Shell,
    Solid,
)
from .values import Point3, Scalar, ScalarInput, point3, scalar


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_faces(
    faces: Face | Sequence[Face],
    name: str,
) -> tuple[Face, ...]:
    values: tuple[Face, ...]
    if isinstance(faces, Face):
        values = (faces,)
    elif isinstance(faces, Sequence) and not isinstance(faces, (str, bytes)):
        values = tuple(faces)
    else:
        raise TypeError(f"{name} expects Face or a sequence of Face")
    if not values:
        raise ValueError(f"{name} requires at least one Face")
    if not all(isinstance(face, Face) for face in values):
        raise TypeError(f"{name} expects only Face values")
    return values


def _require_points(
    points: Sequence[Point3],
    *,
    minimum: int,
    name: str,
) -> tuple[Point3, ...]:
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise TypeError(f"{name} expects a sequence of Point3")
    values = tuple(points)
    if len(values) < minimum:
        raise ValueError(f"{name} requires at least {minimum} points")
    if not all(isinstance(point, Point3) for point in values):
        raise TypeError(f"{name} expects only Point3 values")
    return values


def _require_polyhedron_faces(
    faces: Iterable[Iterable[int]],
    point_count: int,
    name: str,
) -> tuple[tuple[int, ...], ...]:
    if isinstance(faces, (str, bytes)) or not isinstance(faces, Iterable):
        raise TypeError(f"{name} faces must be a sequence")
    result: list[tuple[int, ...]] = []
    for face in faces:
        if isinstance(face, (str, bytes)) or not isinstance(face, Iterable):
            raise TypeError(f"{name} faces must contain index sequences")
        raw_indices = tuple(face)
        indices = tuple(int(index) for index in raw_indices)
        if len(indices) < 3:
            raise ValueError(f"{name} faces must contain at least three indices")
        if not all(
            isinstance(index, Integral) and not isinstance(index, bool)
            for index in raw_indices
        ):
            raise TypeError(f"{name} face indices must be int")
        if any(index < 0 or index >= point_count for index in indices):
            raise IndexError(f"{name} face index is outside the point sequence")
        result.append(indices)
    if not result:
        raise ValueError(f"{name} requires at least one face")
    return tuple(result)


def _require_qhull_options(value: str | None, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{name} qhull_options must be str or None")
    return value


def _as_scalar(value: ScalarInput) -> Scalar:
    if isinstance(value, Scalar):
        return value
    return scalar(value)


@operation(
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.make_shell",
    operation_version="1",
)
def make_shell(faces: Face | Sequence[Face], /) -> Shell:
    values = _require_faces(faces, "make_shell")
    return Shell(ops.make_shell(tuple(face._legacy() for face in values)))


@operation(
    result=SOLID_SPEC,
    returns=Solid,
    operation_id="zencad.typed.fill3d",
    operation_version="1",
)
def fill3d(shell: Shell, /) -> Solid:
    if not isinstance(shell, Shell):
        raise TypeError("fill3d expects Shell")
    return Solid(ops.fill_shell(shell._legacy()))


@operation(
    result=SHELL_SPEC,
    returns=Shell,
    operation_id="zencad.typed.polyhedron_shell",
    operation_version="1",
)
def polyhedron_shell(
    pnts: Sequence[Point3],
    faces_no: Sequence[Sequence[int]],
) -> Shell:
    points = _require_points(pnts, minimum=3, name="polyhedron_shell")
    faces = _require_polyhedron_faces(faces_no, len(points), "polyhedron_shell")
    return Shell(
        ops.polyhedron_shell(tuple(point._resolved() for point in points), faces)
    )


@overload
def polyhedron(
    pnts: Sequence[Point3],
    faces: Sequence[Sequence[int]],
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def polyhedron(
    pnts: Sequence[Point3],
    faces: Sequence[Sequence[int]],
    shell: Literal[True],
) -> Shell: ...


@overload
def polyhedron(
    pnts: Sequence[Point3],
    faces: Sequence[Sequence[int]],
    shell: bool,
) -> Solid | Shell: ...


def polyhedron(
    pnts: Sequence[Point3],
    faces: Sequence[Sequence[int]],
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "polyhedron shell")
    raw_points = tuple(pnts)
    if len(raw_points) < 3:
        raise ValueError("polyhedron requires at least 3 points")
    context = resolve_context(raw_points)
    with using_context(context):
        points = tuple(
            value if isinstance(value, Point3) else point3(value)
            for value in raw_points
        )
        normalized_faces = _require_polyhedron_faces(
            faces,
            len(points),
            "polyhedron",
        )
        result = polyhedron_shell(points, normalized_faces)
    if shell:
        return result
    return fill3d(result)


def convex_hull(
    pnts: Sequence[Point3],
    incremental: bool = False,
    qhull_options: str | None = None,
) -> tuple[tuple[int, ...], ...]:
    """Materialize the numeric triangulation returned by SciPy/Qhull."""

    points = _require_points(pnts, minimum=4, name="convex_hull")
    _require_bool(incremental, "convex_hull incremental")
    options = _require_qhull_options(qhull_options, "convex_hull")
    resolve_context(points)
    return ops.convex_hull_faces(
        tuple(point._resolved() for point in points),
        incremental,
        options,
    )


def _shell_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Solid | Shell]:
    shell = args[1] if len(args) > 1 else kwargs.get("shell", False)
    return Shell if shell is True else Solid


def _shell_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    return SHELL_SPEC if _shell_result_type(args, kwargs) is Shell else SOLID_SPEC


@overload
def convex_hull_shape(
    pnts: Sequence[Point3],
    shell: Literal[False] = False,
    incremental: bool = False,
    qhull_options: str | None = None,
) -> Solid: ...


@overload
def convex_hull_shape(
    pnts: Sequence[Point3],
    shell: Literal[True],
    incremental: bool = False,
    qhull_options: str | None = None,
) -> Shell: ...


@overload
def convex_hull_shape(
    pnts: Sequence[Point3],
    shell: bool,
    incremental: bool = False,
    qhull_options: str | None = None,
) -> Solid | Shell: ...


@operation(
    result=SOLID_SPEC,
    returns=_shell_result_type,
    select_result=_shell_result_spec,
    operation_id="zencad.typed.convex_hull_shape",
    operation_version="1",
)
def convex_hull_shape(
    pnts: Sequence[Point3],
    shell: bool = False,
    incremental: bool = False,
    qhull_options: str | None = None,
) -> Solid | Shell:
    points = _require_points(pnts, minimum=4, name="convex_hull_shape")
    _require_bool(shell, "convex_hull_shape shell")
    _require_bool(incremental, "convex_hull_shape incremental")
    options = _require_qhull_options(qhull_options, "convex_hull_shape")
    resolved = ops.convex_hull_shape(
        tuple(point._resolved() for point in points), incremental, options, shell
    )
    return Shell(resolved) if shell else Solid(resolved)


def _platonic_polyhedron(
    coordinates: Sequence[tuple[ScalarInput, ScalarInput, ScalarInput]],
    faces: Sequence[Sequence[int]],
    shell: bool,
) -> Solid | Shell:
    context = resolve_context(coordinates)
    with using_context(context):
        points = tuple(point3(*coordinate) for coordinate in coordinates)
        return polyhedron(points, faces, shell)


@overload
def tetrahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def tetrahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def tetrahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def tetrahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def tetrahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "tetrahedron shell")
    edge = _as_scalar(a) if a is not None else _as_scalar(r) / math.sqrt(3 / 2) * 2
    half_edge = edge / 2
    face_inradius = edge * math.sqrt(3) / 6
    face_circumradius = edge * math.sqrt(3) / 3
    inradius = edge * math.sqrt(6) / 12
    circumradius = edge * math.sqrt(6) / 4
    return _platonic_polyhedron(
        (
            (0, 0, circumradius),
            (0, face_circumradius, -inradius),
            (-half_edge, -face_inradius, -inradius),
            (half_edge, -face_inradius, -inradius),
        ),
        ((1, 0, 3), (2, 0, 1), (3, 0, 2), (2, 1, 3)),
        shell,
    )


@overload
def hexahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def hexahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def hexahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def hexahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def hexahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "hexahedron shell")
    edge = _as_scalar(a) if a is not None else _as_scalar(r) / math.sqrt(3) * 2
    half_edge = edge / 2
    return _platonic_polyhedron(
        (
            (-half_edge, -half_edge, -half_edge),
            (-half_edge, -half_edge, half_edge),
            (-half_edge, half_edge, -half_edge),
            (-half_edge, half_edge, half_edge),
            (half_edge, -half_edge, -half_edge),
            (half_edge, -half_edge, half_edge),
            (half_edge, half_edge, -half_edge),
            (half_edge, half_edge, half_edge),
        ),
        (
            (0, 1, 3, 2),
            (4, 5, 7, 6),
            (2, 3, 7, 6),
            (0, 1, 5, 4),
            (0, 2, 6, 4),
            (1, 3, 7, 5),
        ),
        shell,
    )


@overload
def octahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def octahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def octahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def octahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def octahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "octahedron shell")
    edge = _as_scalar(a) if a is not None else _as_scalar(r) / math.sqrt(2) * 2
    half_edge = edge / 2
    circumradius = edge * math.sqrt(2) / 2
    return _platonic_polyhedron(
        (
            (0, 0, circumradius),
            (-half_edge, half_edge, 0),
            (half_edge, half_edge, 0),
            (half_edge, -half_edge, 0),
            (-half_edge, -half_edge, 0),
            (0, 0, -circumradius),
        ),
        (
            (1, 0, 2),
            (2, 0, 3),
            (3, 0, 4),
            (4, 0, 1),
            (5, 1, 2),
            (5, 2, 3),
            (5, 3, 4),
            (4, 1, 5),
        ),
        shell,
    )


@overload
def dodecahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def dodecahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def dodecahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def dodecahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def dodecahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "dodecahedron shell")
    edge = (
        _as_scalar(a)
        if a is not None
        else _as_scalar(r) / (math.sqrt(3) * (1 + math.sqrt(5)) / 2) * 2
    )
    cube = edge * (1 + math.sqrt(5)) / 4
    zero = edge * 0
    cuboid = edge * (3 + math.sqrt(5)) / 4
    half_edge = edge / 2
    return _platonic_polyhedron(
        (
            (zero, cuboid, half_edge),
            (zero, cuboid, -half_edge),
            (zero, -cuboid, half_edge),
            (zero, -cuboid, -half_edge),
            (half_edge, zero, cuboid),
            (half_edge, zero, -cuboid),
            (-half_edge, zero, cuboid),
            (-half_edge, zero, -cuboid),
            (cube, cube, cube),
            (cube, cube, -cube),
            (cube, -cube, cube),
            (cube, -cube, -cube),
            (-cube, cube, cube),
            (-cube, cube, -cube),
            (-cube, -cube, cube),
            (-cube, -cube, -cube),
            (cuboid, half_edge, zero),
            (cuboid, -half_edge, zero),
            (-cuboid, half_edge, zero),
            (-cuboid, -half_edge, zero),
        ),
        (
            (8, 16, 9, 1, 0),
            (12, 6, 4, 8, 0),
            (1, 13, 18, 12, 0),
            (9, 5, 7, 13, 1),
            (14, 19, 15, 3, 2),
            (3, 11, 17, 10, 2),
            (10, 4, 6, 14, 2),
            (15, 7, 5, 11, 3),
            (10, 17, 16, 8, 4),
            (9, 16, 17, 11, 5),
            (12, 18, 19, 14, 6),
            (15, 19, 18, 13, 7),
        ),
        shell,
    )


@overload
def icosahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def icosahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def icosahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def icosahedron(
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def icosahedron(
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    _require_bool(shell, "icosahedron shell")
    edge = (
        _as_scalar(a)
        if a is not None
        else _as_scalar(r)
        / (math.sqrt((5 - math.sqrt(5)) / 2) * (1 + math.sqrt(5)) / 2)
        * 2
    )
    zero = edge * 0
    half_edge = edge / 2
    golden = edge * (1 + math.sqrt(5)) / 4
    return _platonic_polyhedron(
        (
            (golden, zero, half_edge),
            (golden, zero, -half_edge),
            (-golden, zero, half_edge),
            (-golden, zero, -half_edge),
            (half_edge, golden, zero),
            (half_edge, -golden, zero),
            (-half_edge, golden, zero),
            (-half_edge, -golden, zero),
            (zero, half_edge, golden),
            (zero, half_edge, -golden),
            (zero, -half_edge, golden),
            (zero, -half_edge, -golden),
        ),
        (
            (1, 0, 5),
            (4, 0, 1),
            (5, 0, 10),
            (8, 0, 4),
            (10, 0, 8),
            (4, 1, 9),
            (9, 1, 11),
            (11, 1, 5),
            (3, 2, 6),
            (6, 2, 8),
            (7, 2, 3),
            (8, 2, 10),
            (10, 2, 7),
            (7, 3, 11),
            (9, 3, 6),
            (11, 3, 9),
            (6, 4, 9),
            (8, 4, 6),
            (7, 5, 10),
            (11, 5, 7),
        ),
        shell,
    )


@overload
def platonic(
    nfaces: int,
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: Literal[False] = False,
) -> Solid: ...


@overload
def platonic(
    nfaces: int,
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    *,
    shell: Literal[True],
) -> Shell: ...


@overload
def platonic(
    nfaces: int,
    r: ScalarInput,
    a: ScalarInput | None,
    shell: Literal[True],
) -> Shell: ...


@overload
def platonic(
    nfaces: int,
    r: ScalarInput,
    a: ScalarInput | None,
    shell: bool,
) -> Solid | Shell: ...


def platonic(
    nfaces: int,
    r: ScalarInput = 1,
    a: ScalarInput | None = None,
    shell: bool = False,
) -> Solid | Shell:
    if isinstance(nfaces, bool) or not isinstance(nfaces, int):
        raise TypeError("platonic nfaces must be int")
    _require_bool(shell, "platonic shell")
    factories = {
        4: tetrahedron,
        6: hexahedron,
        8: octahedron,
        12: dodecahedron,
        20: icosahedron,
    }
    try:
        factory = factories[nfaces]
    except KeyError as exception:
        raise ValueError(
            "platonic nfaces must be one of 4, 6, 8, 12, 20"
        ) from exception
    return factory(r, a, shell)


__all__ = [
    "convex_hull",
    "convex_hull_shape",
    "dodecahedron",
    "fill3d",
    "hexahedron",
    "icosahedron",
    "make_shell",
    "octahedron",
    "platonic",
    "polyhedron",
    "polyhedron_shell",
    "tetrahedron",
]
