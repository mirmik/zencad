from OCC.Core.AIS import AIS_InteractiveObject, AIS_Shape, AIS_Axis

from shape import Shape
from color import Color, default_color
from axis  import Axis

class InteractiveObject:
	def __init__(self, iobj):
		self.ais_object = iobj

class ShapeInteractiveObject(InteractiveObject):
	def __init__(self, shape, color):
		self.shape = shape
		self.color = color
		
		ais_object = AIS_Shape(self.shape._shp)

		if self.color is not None:
			ais_object.SetColor(self.color.to_Quantity_Color())
		else:
			ais_object.SetColor(default_color().to_Quantity_Color())	

		super().__init__(ais_object)

class AxisInteractiveObject(InteractiveObject):
	def __init__(self, axis, color):
		self.axis = axis
		self.color = color

		ais_object = AIS_Axis(axis.to_Geom_Line())

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

