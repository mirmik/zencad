import pyservoce
import evalcache

from zencad.util import deg, point3, vector3
from zencad.lazifier import lazy, LazyObjectShape
from zencad.geom.boolean import *

import sys
import operator
import numpy as np

DEF_MTRANS_ARRAY = False
DEF_MTRANS_UNIT = False

# Replace pyservoce transformation __call__ method
# for support lazy objects.
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
def rotate(a, v):
	return pyservoce.rotate(a, vector3(v))


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
	"""
		fuse: True - вернуть объединение. False - вернуть массив.
		multiply_interactive: True - делать копии интерактивных объектов и юнитов.
	"""
	def __init__(self, transes, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
		self.transes = transes
		self.array = array
		self.unit = unit

	def __call__(self, shp):
		if isinstance(shp, (
					pyservoce.interactive_object, 
					zencad.assemble.unit)):
			rets = []
			clones = [shp.copy() for i in range(len(self.transes)-1)]
			objects = [shp] + clones

			lst = [ obj.transform(t) for obj, t in zip(objects, self.transes) ]
			
			if self.array:
				return lst
			else:
				return zencad.assemble.unit(parts=lst)

		else:
			lst = [t(shp) for t in self.transes]
			if self.array:
				return lst
	
			if self.unit:
				return zencad.assemble.unit(parts=lst)
	
			return union(lst)

def multitrans(transes, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
	return multitransform(transes, array=array, unit=unit)


def nulltrans():
	return translate(0, 0, 0)


def sqrmirror(array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
	return multitransform([nulltrans(), mirrorYZ(), mirrorXZ(), mirrorZ()], array=array, unit=unit)

def sqrtrans(*args, **kwargs):
	print("sqrtrans renamed. use sqrmirror instead")
	return sqrmirror(*args, **kwargs)

#def rotate_array(n, fuse=DEF_MTRANS_ARRAY):
#	transes = [
#		rotateZ(angle) for angle in np.linspace(0, deg(360), num=n, endpoint=False)
#	]
#	return multitrans(transes, fuse=fuse)

def rotate_array(n, yaw=deg(360), endpoint=False, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
	lspace = np.linspace(0, yaw, num=n, endpoint=endpoint)
	transes = [	rotateZ(a) for a in lspace	]
	return multitrans(transes, array=array, unit=unit)


def rotate_array2(n, r=None, yaw=(0,deg(360)), roll=(0,0), endpoint=False, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
	lspace1 = np.linspace(yaw[0], yaw[1], num=n, endpoint=endpoint)
	lspace2 = np.linspace(roll[0], roll[1], num=n, endpoint=endpoint)

	transes = [
		rotateZ(a) * right(r) * rotateX(deg(90)) * rotateZ(a2) for a, a2 in zip(lspace1, lspace2)
	]

	return multitrans(transes, array=array, unit=unit)

def short_rotate(f, t):
	_f, _t = vector3(f), vector3(t)
	if _f.early(_t, 0.000000000001):
		return nulltrans()
	return pyservoce.short_rotate(t=_t, f=_f)