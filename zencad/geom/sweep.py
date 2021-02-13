from zencad.shape import Shape, shape_generator
from zencad.lazy import *
from zencad.util import vector3
from zencad.trans import translate

from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism


def _extrude(base, vec, center=False):
	if type(vec) in (float, int):
		vec = vector3(0,0,vec)

	if center:
		trs = translate(-vec / 2);
		return _extrude(trs(base), vec)

	print(base.Shape().ShapeType())

	# Если в объекте есть только один face, но сам объект не face,
	# извлекаем face и применяем влгоритм на нём. 
	if base.Shape().ShapeType() in (TopAbs_SOLID):
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
def extrude(*args, **kwargs): 
	return _extrude(*args, **kwargs)

def linear_extrude(base, vec, center=False):
	return extrude(base, vec, center)