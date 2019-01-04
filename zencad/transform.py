import pyservoce
import evalcache

from zencad.util import deg, point3
from zencad.lazifier import lazy, LazyObjectShape
from zencad.boolean import *

import sys
import operator
import numpy as np

class LazyObjectTransformGenerator(evalcache.LazyObject):
	def __init__(self, *args, **kwargs): evalcache.LazyObject.__init__(self, *args, **kwargs)
	def __call__(self, *args, **kwargs): return evalcache.lazy.lazyinvoke(self, self, args, kwargs, encache=False, decache=False, cls=LazyObjectTransform)

class LazyObjectTransform(evalcache.LazyObject):
	def __init__(self, *args, **kwargs): evalcache.LazyObject.__init__(self, *args, **kwargs)
	def __mul__(self, oth): return evalcache.lazy.lazyinvoke(self, operator.__mul__, (self, oth), encache=False, decache=False, cls=LazyObjectTransform)
	def __call__(self, *args, **kwargs): return evalcache.lazy.lazyinvoke(self, self, args, kwargs, encache=False, decache=False, cls=LazyObjectShape)
	
evalcache.lazy.hashfuncs[LazyObjectTransform] = evalcache.lazy.updatehash_LazyObject
evalcache.lazy.hashfuncs[LazyObjectTransformGenerator] = evalcache.lazy.updatehash_LazyObject

@lazy.lazy(cls=LazyObjectTransformGenerator)
def translate(*args, **kwargs): return pyservoce.translate(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def up(*args, **kwargs): return pyservoce.up(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def down(*args, **kwargs): return pyservoce.down(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def left(*args, **kwargs): return pyservoce.left(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def right(*args, **kwargs): return pyservoce.right(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def forw(*args, **kwargs): return pyservoce.forw(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def back(*args, **kwargs): return pyservoce.back(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def rotateX(*args, **kwargs): return pyservoce.rotateX(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def rotateY(*args, **kwargs): return pyservoce.rotateY(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def rotateZ(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorXZ(*args, **kwargs): return pyservoce.mirrorXZ(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorYZ(*args, **kwargs): return pyservoce.mirrorYZ(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorXY(*args, **kwargs): return pyservoce.mirrorXY(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorX(*args, **kwargs): return pyservoce.mirrorX(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorY(*args, **kwargs): return pyservoce.mirrorY(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def mirrorZ(*args, **kwargs): return pyservoce.mirrorZ(*args, **kwargs)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def scale(factor, center): return pyservoce.scale(factor, point3(center).to_servoce())

@lazy.lazy(cls=LazyObjectTransformGenerator)
def scaleX(factor): return pyservoce.scaleX(factor)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def scaleY(factor): return pyservoce.scaleY(factor)

@lazy.lazy(cls=LazyObjectTransformGenerator)
def scaleZ(factor): return pyservoce.scaleZ(factor)

class multitransform:
	def __init__(self, transes):
		self.transes = transes

	def __call__(self, shp):
		return union([t(shp) for t in self.transes])

def multitrans(transes):
	return multitransform(transes)

def nulltrans(): return translate(0,0,0) 

def sqrtrans(): return multitransform([ 
	nulltrans(), 
	mirrorYZ(),
	mirrorXZ(), 
	mirrorZ() 
])

def rotate_array(n):
	transes = [rotateZ(angle) for angle in np.linspace(0, deg(360), num=n, endpoint=False)]
	return multitrans(transes) 