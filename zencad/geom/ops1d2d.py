import pyservoce
import evalcache

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.util import points, vectors


@lazy.lazy(cls=shape_generator)
def fill(*args, **kwargs):
    return pyservoce.fill(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def interpolate(pnts, tangs=[], closed=False):
    return pyservoce.interpolate(points(pnts), vectors(tangs), closed)

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
            if strt.early(l_strt, 1e-5):
                strt = l_fini
                del lst[i]
                res.insert(0, l)
                break

            elif strt.early(l_fini, 1e-5):
                strt = l_strt
                del lst[i]
                res.insert(0, l)
                break

            elif fini.early(l_strt, 1e-5):
                fini = l_fini
                del lst[i]
                res.append(l)
                break

            elif fini.early(l_fini, 1e-5):
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
        if l.shapetype() == "edge":
            ret.append(l)
        elif l.shapetype() == "wire":
            ret.extend(l.edges())
        else:
            raise Exception("_wires_to_edges : unresolved input type")

    return ret

def _sew_wire(lst, sort=True):
    lst = evalcache.unlazy_if_need(lst)
    lst = _wires_to_edges(lst)

    if sort:
        lst = _sort_wires(lst)

    return pyservoce.make_wire(lst)

def _sew_shell(lst):
    return pyservoce.make_shell(lst)

@lazy.lazy(cls=shape_generator)
def sew(lst, sort=True):
    if lst[0].shapetype()=="face" or lst[0].shapetype()=="shell":
        return _sew_shell(lst)
    else:
        return _sew_wire(lst, sort)


@lazy.lazy(cls=shape_generator)
def fillet2d(shp, r, refs=None):
    if refs is None:
        return pyservoce.fillet2d(shp, r)
    else:
        return pyservoce.fillet2d(shp, r, points(refs))


@lazy.lazy(cls=shape_generator)
def chamfer2d(shp, r, refs=None):
    if refs is None:
        return pyservoce.chamfer2d(shp, r)
    else:
        return pyservoce.chamfer2d(shp, r, points(refs))


@lazy.lazy(cls=shape_generator)
def fix_face(f):
    return pyservoce.fix_face(f)