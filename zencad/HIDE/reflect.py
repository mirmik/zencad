import pyservoce

"""
Подменяем методы рефлексии.
"""

def __replace_reflect_method(cls, mtd):
	omtd = getattr(cls, mtd)

	def nmtd(shp, filter=None):
		if filter is None:
			return omtd(shp)

		else:
			arr = omtd(shp)
			return [ a for a in arr if filter(a) ]

	setattr(cls, mtd, nmtd)

__replace_reflect_method(pyservoce.Shape, "vertices")
__replace_reflect_method(pyservoce.Shape, "edges")
__replace_reflect_method(pyservoce.Shape, "wires")
__replace_reflect_method(pyservoce.Shape, "faces")
__replace_reflect_method(pyservoce.Shape, "shells")
__replace_reflect_method(pyservoce.Shape, "solids")
__replace_reflect_method(pyservoce.Shape, "compsolids")
__replace_reflect_method(pyservoce.Shape, "compounds")

