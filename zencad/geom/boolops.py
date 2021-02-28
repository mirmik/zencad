from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCC.Core.TopoDS import TopoDS_Shape

from zencad.shape import shape_generator, Shape
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

    for i in range(len(lst)):
        ret = occ_pair_difference(ret, lst[i].Shape())

    return Shape(ret)


def _intersect(lst):
    ret = lst[0].Shape()

    for i in range(len(lst)):
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
