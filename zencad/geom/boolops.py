from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common, BRepAlgoAPI_Section
from OCC.Core.TopoDS import TopoDS_Shape

from zencad.geom.shape import shape_generator, Shape
from zencad.lazifier import lazy
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


@lazy.lazy(cls=shape_generator)
def union(lst):
    return _union(lst)


@lazy.lazy(cls=shape_generator)
def intersect(lst):
    return _intersect(lst)


@lazy.lazy(cls=shape_generator)
def difference(lst):
    return _difference(lst)


def _section(a, b, pretty):
    algo = BRepAlgoAPI_Section(a.Shape(), b.Shape())

    if pretty:
        algo.ComputePCurveOn1(True)
        algo.Approximation(True)

    algo.Build()
    if not algo.IsDone():
        printf("warn: section algotithm failed\n")

    return Shape(algo.Shape())


@lazy.lazy(cls=shape_generator)
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
