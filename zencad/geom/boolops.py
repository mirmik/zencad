import builtins as _builtins
from collections.abc import Sequence as _Sequence

from OCP.BOPAlgo import BOPAlgo_Splitter
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.GeomAbs import GeomAbs_Plane
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

from zencad.geom.shape import shape_generator, Shape
from zencad._eager import eager
from zencad.geom.boolops_base import occ_pair_union, occ_pair_difference, occ_pair_intersect


def _union(lst):
    if len(lst) == 1:
        return lst[0]

    nrsize = 0
    rsize = len(lst) // 2 + len(lst) % 2

    narr = [TopoDS_Shape() for i in range(rsize)]

    for i in range(len(lst) // 2):
        narr[i] = occ_pair_union(lst[i].Shape(), lst[len(lst) - i - 1].Shape())

    if len(lst) % 2:
        narr[rsize - 1] = lst[len(lst) // 2].Shape()

    while rsize != 1:
        nrsize = rsize // 2 + rsize % 2

        for i in range(rsize // 2):
            narr[i] = occ_pair_union(narr[i], narr[rsize - i - 1])

        if rsize % 2:
            narr[nrsize - 1] = narr[rsize // 2]

        rsize = nrsize

    return Shape(narr[0])


def _difference(lst):
    ret = lst[0].Shape()

    for i in range(1, len(lst)):
        ret = occ_pair_difference(ret, lst[i].Shape())

    return Shape(ret)


def _intersect(lst):
    ret = lst[0].Shape()

    for i in range(1, len(lst)):
        ret = occ_pair_intersect(ret, lst[i].Shape())

    return Shape(ret)


@eager.decorator(cls=shape_generator)
def union(lst):
    return _union(lst)


@eager.decorator(cls=shape_generator)
def intersect(lst):
    return _intersect(lst)


@eager.decorator(cls=shape_generator)
def difference(lst):
    return _difference(lst)


def _solid_sort_key(shape):
    center = shape.center()
    bounds = shape.boundbox()
    return tuple(round(value, 12) for value in (
        center.x,
        center.y,
        center.z,
        bounds.xmin,
        bounds.ymin,
        bounds.zmin,
        bounds.xmax,
        bounds.ymax,
        bounds.zmax,
        shape.mass(),
    ))


def _solid_parts(shape):
    explorer = TopExp_Explorer(shape.Shape(), TopAbs_SOLID)
    parts = []
    while explorer.More():
        parts.append(Shape(TopoDS.Solid_s(explorer.Current())))
        explorer.Next()
    return tuple(sorted(parts, key=_solid_sort_key))


def _split_resolved(body, tools):
    if not isinstance(body, Shape):
        raise TypeError("split body must be a Shape")
    if not tools:
        raise ValueError("split requires at least one tool Shape")
    if not all(isinstance(tool, Shape) for tool in tools):
        raise TypeError("split tools must contain only Shape values")

    original_count = len(_solid_parts(body))
    if original_count == 0:
        raise TypeError("split body must contain at least one solid")

    algorithm = BOPAlgo_Splitter()
    algorithm.SetNonDestructive(True)
    algorithm.AddArgument(body.Shape())
    for tool in tools:
        algorithm.AddTool(tool.Shape())
    algorithm.Perform()
    if algorithm.HasErrors():
        raise ValueError("OCCT splitter failed for the supplied body and tools")

    parts = _solid_parts(Shape(algorithm.Shape()))
    if len(parts) <= original_count:
        raise ValueError("split tools do not divide the body")
    return parts


def _coordinates(value, name):
    try:
        coordinates = (float(value.x), float(value.y), float(value.z))
    except AttributeError:
        try:
            coordinates = tuple(float(item) for item in value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{name} must contain three numeric coordinates") from error
    if len(coordinates) != 3:
        raise TypeError(f"{name} must contain three numeric coordinates")
    return coordinates


def _coordinate_plane(coordinate, axis):
    if isinstance(axis, str):
        normals = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
        try:
            normal = normals[axis.lower()]
        except KeyError as error:
            raise ValueError("slice axis must be 'x', 'y', 'z', or a vector") from error
    else:
        normal = _coordinates(axis, "slice axis")
    try:
        direction = gp_Dir(*normal)
    except Exception as error:
        raise ValueError("slice plane normal must be non-zero") from error
    distance = float(coordinate)
    origin = (
        direction.X() * distance,
        direction.Y() * distance,
        direction.Z() * distance,
    )
    return gp_Pln(gp_Pnt(*origin), direction)


def _resolved_plane(plane, coordinate, axis):
    if plane is None:
        return _coordinate_plane(coordinate, axis)
    if isinstance(plane, Shape):
        if not plane.is_face():
            raise TypeError("slice plane Shape must be a planar face")
        adaptor = BRepAdaptor_Surface(plane.Face())
        if adaptor.GetType() != GeomAbs_Plane:
            raise TypeError("slice plane Shape must be a planar face")
        return adaptor.Plane()
    try:
        origin, normal = plane
    except (TypeError, ValueError) as error:
        raise TypeError("slice plane must be a planar face or (origin, normal)") from error
    origin = _coordinates(origin, "slice plane origin")
    normal = _coordinates(normal, "slice plane normal")
    try:
        return gp_Pln(gp_Pnt(*origin), gp_Dir(*normal))
    except Exception as error:
        raise ValueError("slice plane normal must be non-zero") from error


def _slice_resolved(body, plane, coordinate, axis):
    resolved_plane = _resolved_plane(plane, coordinate, axis)
    tool = Shape(BRepBuilderAPI_MakeFace(resolved_plane).Face())
    parts = _split_resolved(body, (tool,))
    if len(parts) != 2:
        raise ValueError(
            f"slice requires exactly two resulting solids; got {len(parts)}"
        )

    location = resolved_plane.Location()
    direction = resolved_plane.Axis().Direction()

    def signed_center(shape):
        center = shape.center()
        return (
            (center.x - location.X()) * direction.X()
            + (center.y - location.Y()) * direction.Y()
            + (center.z - location.Z()) * direction.Z()
        )

    return tuple(sorted(parts, key=signed_center))


@eager.decorator()
def _split_lazy(body, tools):
    return _split_resolved(body, tools)


@eager.decorator()
def _slice_lazy(body, plane, coordinate, axis):
    return _slice_resolved(body, plane, coordinate, axis)


def _lazy_shape_item(source, index):
    return source[index]


class SplitResult(_Sequence):
    """Lazy, deterministic sequence of solids produced by :func:`split`."""

    __slots__ = ("_source",)

    def __init__(self, source):
        self._source = source

    def __len__(self):
        return len(self._source)

    def __getitem__(self, index):
        if isinstance(index, _builtins.slice):
            return tuple(self[item] for item in range(*index.indices(len(self))))
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("split result indices must be integers or slices")
        return _lazy_shape_item(self._source, index)

    def __iter__(self):
        for index in range(len(self)):
            yield self[index]

    def __repr__(self):
        return f"SplitResult({tuple(self)!r})"


class SliceResult(_Sequence):
    """Ordered pair whose ``lower`` and ``upper`` members follow plane normal."""

    __slots__ = ("lower", "upper")

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __len__(self):
        return 2

    def __getitem__(self, index):
        return (self.lower, self.upper)[index]


def split(body, tools):
    """Partition a solid body with one or more Shape tools.

    The returned solids are ordered deterministically. Evaluation raises
    ``ValueError`` when the tools do not actually divide the body.
    """

    if isinstance(tools, Shape):
        tools = (tools,)
    else:
        try:
            tools = tuple(tools)
        except TypeError as error:
            raise TypeError("split tools must be a Shape or an iterable of Shapes") from error
    if not tools:
        raise ValueError("split requires at least one tool Shape")
    return SplitResult(_split_lazy(body, tools))


def slice(body, z=0, *, axis="z", plane=None):
    """Split a body into the negative and positive sides of a plane.

    ``z`` is the signed coordinate along ``axis``. Alternatively, ``plane``
    accepts a planar face or an ``(origin, normal)`` pair. A non-dividing plane
    and a result other than two solids raise ``ValueError`` on evaluation.
    """

    if plane is not None and z != 0:
        raise TypeError("slice accepts either z/axis or plane, not both")
    source = _slice_lazy(body, plane, z, axis)
    return SliceResult(
        _lazy_shape_item(source, 0),
        _lazy_shape_item(source, 1),
    )


def _section(a, b, pretty):
    algo = BRepAlgoAPI_Section(a.Shape(), b.Shape())

    if pretty:
        algo.ComputePCurveOn1(True)
        algo.Approximation(True)

    algo.Build()
    if not algo.IsDone():
        print("warn: section algorithm failed")

    return Shape(algo.Shape())


@eager.decorator(cls=shape_generator)
def section(a, b=0):
    """
        Make section between 'a' and 'b'.
        Oposite the intersect, which finds the intersection of bodies,
        the section finds the intersection of the shells of bodies.

        Arguments:
        a, b - is pair of algorithm arguments. The algorithm is commutative.
            a and b can be numeric or vector. In that case algorithm find
            section with a given plane.
    """
    import zencad.util
    from zencad.geom.solid import _halfspace

    def to_halfspace_if_need(x):
        if isinstance(x, (tuple, list, zencad.util.vector3)):
            vec = zencad.util.vector3(x)
            return (
                zencad.transform.translate(*vec) *
                zencad.transform.short_rotate(f=(0, 0, 1), t=vec)
            )(_halfspace())

        elif isinstance(x, (int, float)):
            return _halfspace().up(x)

        return x

    result = _section(
        to_halfspace_if_need(a),
        to_halfspace_if_need(b),
        False
    )

    return result
