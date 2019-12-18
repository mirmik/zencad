import evalcache
import evalcache.dircache
import evalcache.dircache_v2
from evalcache.lazyfile import LazyFile

import pyservoce
import hashlib
import os

from zencad.util import points, vector3, point3

cachepath = os.path.expanduser("~/.zencadcache")
algo = hashlib.sha512

lazy = evalcache.Lazy(
    cache=evalcache.dircache_v2.DirCache_v2(cachepath), 
    algo=algo, 
    onbool=True,
    onstr=True
)

def _scale_do(self, factor, center=pyservoce.libservoce.point3(0,0,0)):
    if isinstance(factor, (list, tuple)):
        return pyservoce.Shape.scaleXYZ(self, factor[0], factor[1], factor[2])
    return pyservoce.Shape.scale(self, factor, point3(center))

class LazyObjectShape(evalcache.LazyObject):
    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def translate(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.translate,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def up(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.up,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def down(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.down,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def left(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.left,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def right(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.right,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def back(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.back,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def rotate(self, ax, angle):
        return self.lazyinvoke(
            pyservoce.Shape.rotate,
            (self, vector3(ax), angle),
            {},
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def rotateX(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.rotateX,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def rotateY(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.rotateY,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def rotateZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.rotateZ,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorX(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorX,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorY(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorY,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorZ,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorXY(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorXY,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorXZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorXZ,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def mirrorYZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.mirrorYZ,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def scale(self, *args, **kwargs):
        return self.lazyinvoke(
            _scale_do,
            (self, *args),
            kwargs,
            encache=False,
            decache=False,
            cls=LazyObjectShape,
        )

    def scaleX(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleX,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleY(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleY,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleZ,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleXY(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleXY,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleYZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleYZ,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleXZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleXZ,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

    def scaleXYZ(self, *args, **kwargs):
        return self.lazyinvoke(
            pyservoce.Shape.scaleXYZ,
            (self, *args),
            kwargs,
            encache=True,
            decache=True,
            cls=LazyObjectShape,
        )

class nocached_shape_generator(evalcache.LazyObject):
    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.lazyinvoke(
            self, args, kwargs, encache=False, decache=False, cls=LazyObjectShape
        )


class shape_generator(evalcache.LazyObject):
    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.lazyinvoke(self, args, kwargs, cls=LazyObjectShape)


evalcache.lazy.hashfuncs[LazyObjectShape] = evalcache.lazy.updatehash_LazyObject
evalcache.lazy.hashfuncs[shape_generator] = evalcache.lazy.updatehash_LazyObject
evalcache.lazy.hashfuncs[
    nocached_shape_generator
] = evalcache.lazy.updatehash_LazyObject


def disable_cache():
    lazy.encache = False
    lazy.decache = False


def test_mode():
    disable_cache()
    lazy.diag = True


def restore_default_lazyopts():
    lazy.cache = evalcache.dircache_v2.DirCache_v2(cachepath)
    lazy.encache = True
    lazy.decache = True
    lazy.diag = False
    lazy.diag_values = False
    lazy.print_invokes = False


diag = None
ensave = None
desave = None
onplace = None


def disable_lazy():
    global ensave, desave, onplace
    ensave = lazy.encache
    desave = lazy.decache
    diag = lazy.diag
    onplace = lazy.onplace
    lazy.diag = False
    lazy.encache = False
    lazy.decache = False
    lazy.onplace = True


def restore_lazy():
    lazy.onplace = onplace
    lazy.encache = ensave
    lazy.decache = desave
    lazy.diag = diag
