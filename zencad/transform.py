import pyservoce
from zencad.util import deg, point3
from zencad.lazy import lazy
from zencad.boolean import *

import numpy as np

@lazy
def translate(*args, **kwargs): return pyservoce.translate(*args, **kwargs)

@lazy
def up(*args, **kwargs): return pyservoce.up(*args, **kwargs)

@lazy
def down(*args, **kwargs): return pyservoce.down(*args, **kwargs)

@lazy
def left(*args, **kwargs): return pyservoce.left(*args, **kwargs)

@lazy
def right(*args, **kwargs): return pyservoce.right(*args, **kwargs)

@lazy
def forw(*args, **kwargs): return pyservoce.forw(*args, **kwargs)

@lazy
def back(*args, **kwargs): return pyservoce.back(*args, **kwargs)

@lazy
def rotateX(*args, **kwargs): return pyservoce.rotateX(*args, **kwargs)

@lazy
def rotateY(*args, **kwargs): return pyservoce.rotateY(*args, **kwargs)

@lazy
def rotateZ(*args, **kwargs): return pyservoce.rotateZ(*args, **kwargs)

@lazy
def mirrorXZ(*args, **kwargs): return pyservoce.mirrorXZ(*args, **kwargs)

@lazy
def mirrorYZ(*args, **kwargs): return pyservoce.mirrorYZ(*args, **kwargs)

@lazy
def mirrorXY(*args, **kwargs): return pyservoce.mirrorXY(*args, **kwargs)

@lazy
def mirrorX(*args, **kwargs): return pyservoce.mirrorX(*args, **kwargs)

@lazy
def mirrorY(*args, **kwargs): return pyservoce.mirrorY(*args, **kwargs)

@lazy
def mirrorZ(*args, **kwargs): return pyservoce.mirrorZ(*args, **kwargs)

@lazy
def scale(factor, center): return pyservoce.scale(factor, point3(center).to_servoce())

@lazy
def scaleX(factor): return pyservoce.scaleX(factor)

@lazy
def scaleY(factor): return pyservoce.scaleY(factor)

@lazy
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