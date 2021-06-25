from zencad.geom.shape import Shape, nocached_shape_generator, shape_generator
from zencad.util import as_indexed
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE

from OCC.Core.gp import gp_Pnt

from zencad.lazifier import lazy
import evalcache
import numpy


def __make_wire(lst):
    mk = BRepBuilderAPI_MakeWire()

    for ptr in lst:
        if ptr.Shape().ShapeType() == TopAbs_WIRE:
            mk.Add(ptr.Wire())
        elif ptr.Shape().ShapeType() == TopAbs_EDGE:
            mk.Add(ptr.Edge())

    return mk.Wire()


def _sort_wires(lst):
    lst = evalcache.unlazy_if_need(lst)
    size = len(lst)

    res = [lst[0]]
    strt = lst[0].endpoints()[0]
    fini = lst[0].endpoints()[1]
    del lst[0]

    stubiter = 0
    while len(res) != size:
        for i, l in enumerate(lst):
            l_strt = l.endpoints()[0]
            l_fini = l.endpoints()[1]

            # TODO: Fix point3 equality in servoce library and change equalities to early methods.
            if numpy.linalg.norm(strt - l_strt) < 1e-5:
                strt = l_fini
                del lst[i]
                res.insert(0, l)
                break

            elif numpy.linalg.norm(strt - l_fini) < 1e-5:
                strt = l_strt
                del lst[i]
                res.insert(0, l)
                break

            elif numpy.linalg.norm(fini - l_strt) < 1e-5:
                fini = l_fini
                del lst[i]
                res.append(l)
                break

            elif numpy.linalg.norm(fini - l_fini) < 1e-5:
                fini = l_strt
                del lst[i]
                res.append(l)
                break

        else:
            stubiter += 1

        if stubiter >= 3:
            raise Exception("sew:sorting: Failed to wires sorting")

    return res


def _wires_to_edges(lst):
    ret = []

    for l in lst:
        if l.is_edge():
            ret.append(l)
        elif l.is_wire():
            ret.extend(l.edges())
        else:
            raise Exception("_wires_to_edges : unresolved input type")

    return ret


def _sew_wire(lst, sort=True):
    from zencad.geom.wire import _make_wire
    lst = evalcache.unlazy_if_need(lst)
    lst = _wires_to_edges(lst)

    if sort:
        lst = _sort_wires(lst)

    return _make_wire(lst)


def _sew_shell(lst):
    from zencad.geom.shell import _make_shell
    return _make_shell(lst)


def _sew(lst, sort=True):
    if lst[0].is_face() or lst[0].is_shell():
        return _sew_shell(lst)
    else:
        return _sew_wire(lst, sort)


@lazy.lazy(cls=shape_generator)
def sew(lst, sort=True):
    return _sew(lst, sort)
