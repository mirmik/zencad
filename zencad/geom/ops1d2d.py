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

def _sew_wire(lst, sort=True):
    lst = evalcache.unlazy_if_need(lst)

    if sort:
        size = len(lst)

        res = [lst[0]]
        strt = lst[0].endpoints()[0]
        fini = lst[0].endpoints()[1]
        lst.remove(lst[0])

        stubiter = 0
        while len(res) != size:
            for l in lst:
                l_strt = l.endpoints()[0]
                l_fini = l.endpoints()[1]

                # TODO: Fix point3 equality in servoce library and change equalities to early methods.
                if strt == l_strt:
                    strt = l_fini
                    lst.remove(l)
                    res.insert(0, l)
                    break

                elif strt == l_fini:
                    strt = l_strt
                    lst.remove(l)
                    res.insert(0, l)
                    break

                elif fini == l_strt:
                    fini = l_fini
                    lst.remove(l)
                    res.append(l)
                    break

                elif fini == l_fini:
                    fini = l_fini
                    lst.remove(l)
                    res.append(l)
                    break

            else:
                stubiter += 1

            if stubiter >= 3:
                raise Exception("sew:sorting: Failed to wires sorting")

        lst = res

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
