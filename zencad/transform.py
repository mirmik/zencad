import pyservoce
import evalcache

from zencad.util import deg, point3, vector3
from zencad.lazifier import lazy, LazyObjectShape
from zencad.geom.boolean import *

import sys
import operator
import numpy as np

# Объекты трансформации более не являются хешируемыми.
# Скорости хеширование трансформаций особо не добавляет, а путаницу вносит.

#class LazyObjectTransformGeneratorCached(evalcache.LazyObject):
#    def __init__(self, *args, **kwargs):
#        evalcache.LazyObject.__init__(self, *args, **kwargs)
#
#    def __call__(self, *args, **kwargs):
#        return evalcache.lazy.lazyinvoke(
#            self,
#            self,
#            args,
#            kwargs,
#            encache=False,
#            decache=False,
#            cls=LazyObjectTransformCached,
#        )
#
#
#class LazyObjectTransformGeneratorNoCached(evalcache.LazyObject):
#    def __init__(self, *args, **kwargs):
#        evalcache.LazyObject.__init__(self, *args, **kwargs)
#
#    def __call__(self, *args, **kwargs):
#        return evalcache.lazy.lazyinvoke(
#            self,
#            self,
#            args,
#            kwargs,
#            encache=False,
#            decache=False,
#            cls=LazyObjectTransformNoCached,
#        )
#
#
#class LazyObjectTransformCached(evalcache.LazyObject):
#    def __init__(self, *args, **kwargs):
#        evalcache.LazyObject.__init__(self, *args, **kwargs)
#
#    def __mul__(self, oth):
#        return evalcache.lazy.lazyinvoke(
#            self,
#            operator.__mul__,
#            (self, oth),
#            encache=False,
#            decache=False,
#            cls=LazyObjectTransformCached,
#        )
#
#    def __call__(self, *args, **kwargs):
#        return evalcache.lazy.lazyinvoke(self, self, args, kwargs, cls=LazyObjectShape)
#
#
#class LazyObjectTransformNoCached(evalcache.LazyObject):
#    def __init__(self, *args, **kwargs):
#        evalcache.LazyObject.__init__(self, *args, **kwargs)
#
#    def __mul__(self, oth):
#        return evalcache.lazy.lazyinvoke(
#            self,
#            operator.__mul__,
#            (self, oth),
#            encache=False,
#            decache=False,
#            cls=LazyObjectTransformCached,
#        )
#
#    def __call__(self, *args, **kwargs):
#        return evalcache.lazy.lazyinvoke(
#            self, self, args, kwargs, encache=False, decache=False, cls=LazyObjectShape
#        )


#evalcache.lazy.hashfuncs[
#    LazyObjectTransformNoCached
#] = evalcache.lazy.updatehash_LazyObject
#evalcache.lazy.hashfuncs[
#    LazyObjectTransformCached
#] = evalcache.lazy.updatehash_LazyObject
#evalcache.lazy.hashfuncs[
#    LazyObjectTransformGeneratorCached
#] = evalcache.lazy.updatehash_LazyObject
#evalcache.lazy.hashfuncs[
#    LazyObjectTransformGeneratorNoCached
#] = evalcache.lazy.updatehash_LazyObject

native_call = pyservoce.transformation.__call__

def transform_call(self, arg):
    if isinstance(arg, evalcache.LazyObject):
        return arg.transform(self)

    return native_call(self, arg)

pyservoce.transformation.__call__ = transform_call


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def translate(*args, **kwargs):
    return pyservoce.translate(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def up(*args, **kwargs):
    return pyservoce.up(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def down(*args, **kwargs):
    return pyservoce.down(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def left(*args, **kwargs):
    return pyservoce.left(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def right(*args, **kwargs):
    return pyservoce.right(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def forw(*args, **kwargs):
    return pyservoce.forw(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def back(*args, **kwargs):
    return pyservoce.back(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def rotate(ax, angle):
    return pyservoce.rotate(vector3(ax), angle)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def rotateX(*args, **kwargs):
    return pyservoce.rotateX(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def rotateY(*args, **kwargs):
    return pyservoce.rotateY(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def rotateZ(*args, **kwargs):
    return pyservoce.rotateZ(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorXZ(*args, **kwargs):
    return pyservoce.mirrorXZ(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorYZ(*args, **kwargs):
    return pyservoce.mirrorYZ(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorXY(*args, **kwargs):
    return pyservoce.mirrorXY(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorX(*args, **kwargs):
    return pyservoce.mirrorX(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorY(*args, **kwargs):
    return pyservoce.mirrorY(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorNoCached)
def mirrorZ(*args, **kwargs):
    return pyservoce.mirrorZ(*args, **kwargs)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scale(factor, center):
    if factor is list or factor is tuple:
        return pyservoce.scaleXYZ(factor[0], factor[1], factor[2])
    return pyservoce.scale(factor, point3(center).to_servoce())


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleX(factor):
    return pyservoce.scaleX(factor)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleY(factor):
    return pyservoce.scaleY(factor)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleZ(factor):
    return pyservoce.scaleZ(factor)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleXY(x,y):
    return pyservoce.scaleXY(x,y)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleYZ(y,z):
    return pyservoce.scaleYZ(y,z)


#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleXZ(x,z):
    return pyservoce.scaleXZ(x,z)

#@lazy.lazy(cls=LazyObjectTransformGeneratorCached)
def scaleXYZ(x,y,z):
    return pyservoce.scaleXYZ(x,y,z)


class multitransform:
    def __init__(self, transes):
        self.transes = transes

    def __call__(self, shp):
        return union([t(shp) for t in self.transes])


def multitrans(transes):
    return multitransform(transes)


def nulltrans():
    return translate(0, 0, 0)


def sqrtrans():
    return multitransform([nulltrans(), mirrorYZ(), mirrorXZ(), mirrorZ()])


def rotate_array(n):
    transes = [
        rotateZ(angle) for angle in np.linspace(0, deg(360), num=n, endpoint=False)
    ]
    return multitrans(transes)


def short_rotate(fromvec, tovec):
    _f, _t = vector3(fromvec), vector3(tovec)
    if _f.early(_t, 0.000000000001):
        return nulltrans()
    return pyservoce.short_rotate(_f, _t)