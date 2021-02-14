from zencad.shape import Shape, shape_generator
from zencad.lazy import *
from zencad.util import vector3
from zencad.trans import translate

from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir

from zencad.util import *


def _extrude(base, vec, center=False):
	if type(vec) in (float, int):
		vec = vector3(0,0,vec)
	else:
		vec = vector3(vec)

	if center:
		trs = translate(-vec / 2);
		return _extrude(trs(base), vec)

	# Если в объекте есть только один face, но сам объект не face,
	# извлекаем face и применяем влгоритм на нём. 
	if base.Shape().ShapeType() in (TopAbs_SOLID,):
		faces = base.faces()
		print(faces)
		if len(faces) == 1:
			obj = faces[0]
		else:
			raise Exception("extrude doesn't work with solids")
	else:
		obj = base.Shape()

	return Shape(BRepPrimAPI_MakePrism(obj, vec.Vec()).Shape())

@lazy.lazy(cls=shape_generator)
def extrude(*args, **kwargs): return _extrude(*args, **kwargs)

def linear_extrude(base, vec, center=False):
	return extrude(base, vec, center)


def _revol(proto, r=None, yaw=0.0):
	if r is not None:
		proto = proto.rotX(deg(90)).movX(r)

	ax = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))

	if yaw == 0:
		return Shape(BRepPrimAPI_MakeRevol(proto.Shape(), ax).Shape())
	else:
		return Shape(BRepPrimAPI_MakeRevol(proto.Shape(), ax, yaw).Shape())

@lazy.lazy(cls=shape_generator)
def revol(*args, **kwargs): return _revol(*args, **kwargs)


def _loft(arr, smooth=False, shell=False, maxdegree=4):
	builder = BRepOffsetAPI_ThruSections(not shell, not smooth)
	builder.SetMaxDegree(maxdegree)

	for v in arr:
		if v.Shape().ShapeType() == TopAbs_FACE:
			raise Exception("Loft argument must be array of Wires or Edges")

	for r in arr:
		builder.AddWire(r.Wire_orEdgeToWire())
	
	return Shape(builder.Shape())

@lazy.lazy(cls=shape_generator)
def loft(*args, **kwargs): return _loft(*args, **kwargs)
