from OCC.Core.AIS import AIS_InteractiveObject, AIS_Shape, AIS_Axis, AIS_Point
from OCC.Core.Prs3d import Prs3d_LineAspect
from OCC.Core.Quantity import Quantity_NOC_BLACK, Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Aspect import Aspect_TOL_SOLID
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.Geom import Geom_CartesianPoint

from zencad.shape import Shape
from zencad.color import Color, default_color
from zencad.axis  import Axis

class InteractiveObject:
	def __init__(self, iobj):
		self.ais_object = iobj

		aspect = self.ais_object.Attributes().LineAspect()
		aspect.SetColor(Quantity_Color(0,0,0,Quantity_TOC_RGB))
		#Prs3d_LineAspect(Quantity_NOC_BLACK, Aspect_TOL_SOLID, 1)
		self.ais_object.Attributes().SetFaceBoundaryAspect(aspect);

class ShapeInteractiveObject(InteractiveObject):
	def __init__(self, shape, color):
		self.shape = shape
		self.color = color
		
		ais_object = AIS_Shape(self.shape._shp)

		if self.color is None:
			self.color = default_color()

		ais_object.SetColor(self.color.to_Quantity_Color())
		ais_object.SetTransparency(self.color.a)

		super().__init__(ais_object)

class AxisInteractiveObject(InteractiveObject):
	def __init__(self, axis, color):
		self.axis = axis
		self.color = color

		ais_object = AIS_Axis(axis.to_Geom_Line())

		if self.color is not None:
			ais_object.SetColor(self.color.to_Quantity_Color())

		super().__init__(ais_object)

class PointInteractiveObject(InteractiveObject):
	def __init__(self, point, color):
		self.point = point
		self.color = color

		ais_object = AIS_Point(point)

		if self.color is not None:
			ais_object.SetColor(self.color.to_Quantity_Color())

		super().__init__(ais_object)
		
def create_interactive_object(obj, color=None):
	if isinstance(color, (tuple,list)):
		color = Color(*color)

	if isinstance(obj, Shape):
		return ShapeInteractiveObject(obj, color)
	elif isinstance(obj, Axis):
		return AxisInteractiveObject(obj, color)
	elif isinstance(obj, Geom_CartesianPoint):
		return PointInteractiveObject(obj, color)

	else:
		raise Exception("unresolved type", obj.__class__)
