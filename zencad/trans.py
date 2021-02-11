import util3
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax1, gp_Pnt, gp_Dir, gp_Quaternion
from lazifier2 import *

import sys
import numpy
import pickle
import base64 as b64

class Transformation:
	def __init__(self, trsf):
		self._trsf = trsf

	def __call__(self, obj):
		return obj.transform(self)

	def __mul__(self, oth):
		return Transformation(self._trsf.Multiplied(oth._trsf))

	def __getstate__(self):
		scl = self._trsf.ScaleFactor()
		rot = self._trsf.GetRotation()
		tra = self._trsf.TranslationPart()

		return { 
			"scale": scl, 
			"rotate": (rot.X(), rot.Y(), rot.Z(), rot.W()),
			"transl": (tra.X(), tra.Y(), tra.Z()),
		}

	def __setstate__(self, dct):
		scl = dct["scale"]
		rot = dct["rotate"]
		tra = dct["transl"]

		_trsf = gp_Trsf()
		_trsf.SetRotation(*rot)
		_trsf.SetTranslation(*tra)
		_trsf.SetScale(scl)

	def __repr__(self):
		return b64.b64encode(pickle.dumps(self)).decode("utf-8")

def move(*args):
	xyz = util3.as_indexed(args)
	trsf = gp_Trsf()
	trsf.SetTranslation(gp_Vec(args[0], args[1], args[2]))
	return Transformation(trsf)

def translate(*args):
	return move(*args)

def moveX(x): return move(x,0,0)
def moveY(y): return move(0,y,0)
def moveZ(z): return move(0,0,z)
def movX(x): return move(x,0,0)
def movY(y): return move(0,y,0)
def movZ(z): return move(0,0,z)
def translateX(x): return move(x,0,0)
def translateY(y): return move(0,y,0)
def translateZ(z): return move(0,0,z)

def rotate(axis, angle):
	trsf = gp_Trsf();
	trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(gp_Vec(axis[0], axis[1], axis[2]))), angle);
	return Transformation(trsf);
