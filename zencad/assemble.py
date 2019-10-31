import pyservoce
import evalcache
import numpy

import zencad.settings

class ShapeView:
	def __init__(self, sctrl):
		self.sctrl = sctrl

	def set_location(self, trans):
		self.sctrl.set_location(trans)

	def hide(self, en):
		self.sctrl.hide(en)

class unit:
	"""Базовый класс для использования в кинематических цепях и сборках

	Вычисляет свою текущую позицию исходя из дерева построения.
	Держит список наследников, позиция которых считается относительно него.    
	"""

	def __init__(self, 
				parent=None,
				shape=None,
				name=None, 
				location=pyservoce.libservoce.nulltrans()):    
		self.parent = parent
		self.shape = shape
		self.location = evalcache.unlazy_if_need(location)
		self.global_location = self.location
		self.name = name
		self.color = None
		self.dispobjects = []
		self.shapes_holder = []

		self.views = set()
		self.childs = set()

		if parent is not None:
			parent.add_child(self)

	def add_child(self, child):
		child.parent = self
		self.childs.add(child)

	def link(self, child):
		self.add_child(child)

	def location_update(self, deep=True, view=True):
		if self.parent is None:
			self.global_location = self.location

		else:
			self.global_location = self.parent.global_location * self.location

		if deep:
			for c in self.childs:
				c.location_update(deep=True, view=view)

		if view:
			self._apply_view_location(False)

	def relocate(self, location, deep=False, view=True):
		self.location = evalcache.unlazy_if_need(location)
		self.location_update(deep=deep, view=False)

		if view:
			self._apply_view_location(deep=deep)

	def set_objects(self, objects):
		self.dispobjects = objects

	def add_object(self, d):
		self.dispobjects.append(d)

	def add_shape(self, shp, color=zencad.settings.Settings.get_default_color()):
		shp = evalcache.unlazy_if_need(shp)
		controller = pyservoce.interactive_object(shp)
		controller.set_color(pyservoce.color(color))
		self.dispobjects.append(controller)
		self.shapes_holder.append(shp)
		return controller

	def add_triedron(self, length=10, width=1, arrlen=1,
			xcolor=pyservoce.red, ycolor=pyservoce.green, zcolor=pyservoce.blue):
		self.xaxis = pyservoce.draw_arrow(pyservoce.point3(0,0,0), pyservoce.vector3(length,0,0), clr=xcolor, arrlen=arrlen, width=width)
		self.yaxis = pyservoce.draw_arrow(pyservoce.point3(0,0,0), pyservoce.vector3(0,length,0), clr=ycolor, arrlen=arrlen, width=width)
		self.zaxis = pyservoce.draw_arrow(pyservoce.point3(0,0,0), pyservoce.vector3(0,0,length), clr=zcolor, arrlen=arrlen, width=width)

		self.dispobjects.append(self.xaxis)
		self.dispobjects.append(self.yaxis)
		self.dispobjects.append(self.zaxis)

	def set_shape(self, shape):
		self.shape = shape

	def set_color(self, *args, **kwargs):
		self.color = pyservoce.color(*args, **kwargs)

	def print_tree(self, tr=0):
		s = "\t" * tr + str(self) 
		print(s)
		
		for c in self.childs:
			c.print_tree(tr+1)

	def __str__(self):
		if self.name:
			n = self.name
		else:
			n = repr(self)

		if self.shape is None:
			h = "NullShape"
		else:
			h = self.shape.__lazyhexhash__[0:10]

		return str((n,h))

	def _apply_view_location(self, deep):
		"""Перерисовать положения объектов юнита во всех зарегестрированных 
		view. Если deep, применить рекурсивно."""

		for v in self.views:
			v.set_location(self.global_location)

		if deep:
			for c in self.childs:
				c._apply_view_location(deep)
		
	def bind_scene(self, 
				scene, 
				color=zencad.settings.Settings.get_default_color(), 
				deep=True):
		self.location_update(deep)

		for d in self.dispobjects:
			scene.viewer.display(d)
			self.views.add(ShapeView(d))

		if self.shape is not None:
			if self.color is not None:
				color = self.color
	
			shape_view = ShapeView(scene.add(
				evalcache.unlazy_if_need(self.shape), 
				color))
			scene.viewer.display(shape_view.sctrl)
			self.views.add(shape_view)

		self._apply_view_location(deep=False)

		if deep:
			for c in self.childs:
				c.bind_scene(scene, color=color, deep=True)

