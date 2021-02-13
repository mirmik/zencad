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
	def __init__(self, iobj, color):
		self.ais_object = iobj
		self.color = color if color is not None else default_color()

		aspect = self.ais_object.Attributes().LineAspect()
		self.ais_object.Attributes().SetFaceBoundaryAspect(aspect)

		self.set_color(color)

	def set_color(self, color):
		self.ais_object.SetColor(self.color.to_Quantity_Color())
		self.ais_object.SetTransparency(self.color.a)

class ShapeInteractiveObject(InteractiveObject):
	def __init__(self, shape, color):
		self.shape = shape
		super().__init__(AIS_Shape(self.shape._shp), color=color)

class AxisInteractiveObject(InteractiveObject):
	def __init__(self, axis, color):
		self.axis = axis
		super().__init__(AIS_Axis(axis.to_Geom_Line()), color=color)
	

class PointInteractiveObject(InteractiveObject):
	def __init__(self, point, color):
		self.point = point
		super().__init__(AIS_Point(point), color=color)

		
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
