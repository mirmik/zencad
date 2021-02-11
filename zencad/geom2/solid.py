
from shape import Shape
from util3 import as_indexed
import OCC.Core.BRepPrimAPI

from lazifier2 import *

@lazy.lazy(nocache=1)
def box(*args, center=None):
	xyz = as_indexed(args)
	raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(*xyz).Shape()
	return Shape(raw)

@lazy.lazy(nocache=1)
def sphere(r, yaw=None, pitch=None):
	raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeSphere(r).Shape()
	return Shape(raw)

@lazy.lazy(nocache=1)
def cylinder(r, h, yaw=None, center=False):
	raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCylinder(r,h).Shape()
	return Shape(raw)

@lazy.lazy(nocache=1)
def cone(r1, r2, h, yaw=None, center=False):
	raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeCone(r1,r2,h).Shape()
	return Shape(raw)

@lazy.lazy(nocache=1)
def torus(r1, r2, yaw=None, pitch=None):
	raw = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeTorus(r1,r2).Shape()
	return Shape(raw)