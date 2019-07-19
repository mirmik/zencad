import zencad.assemble
import pyservoce

from abc import ABC, abstractmethod

class cynematic_unit(ABC, zencad.assemble.unit):
	"""Кинематическое звено задаётся двумя системами координат,
	входной и выходной. Изменение кинематических параметров изменяет
	положение выходной СК относительно входной"""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.output = zencad.assemble.unit(parent=self)

	@abstractmethod
	def senses(self):
		"""Возвращает кортеж тензоров производной по положению
		по набору кинематических координат
		в собственной системе координат в формате (w, v)"""

		raise NotImplementedError

	@abstractmethod
	def set_coords(self, coords, **kwargs):
		"""Устанавливает модельное положение звена согласно 
		переданным координатам"""
		
		raise NotImplementedError

	def link(self, arg):
		"""Присоединить объект arg к выходной СК.

		Для cynematic_unit метод link переопределяется,
		с тем, чтобы линковка происходила не ко входной, 
		а к выходной СК"""

		self.output.link(arg)

class cynematic_unit_one_axis(cynematic_unit):
	"""Кинематическое звено специального вида,
	взаимное положение СК которого может быть описано одним 3вектором

	ax - вектор, задающий ось и направление. задаётся с точностью до длины.
	mul - линейный коэффициент масштабирования входной координаты.
	"""
	
	def __init__(self, ax, mul=1, **kwargs):
		super().__init__(**kwargs)
		self.coord = 0
		self.ax = pyservoce.vector3(ax)
		self.ax = self.ax.normalize()
		self.mul = mul
		self.axmul = self.ax * self.mul

	#override
	def senses(self):
		return (sensivity(),)

	#override
	def set_coords(self, coords, **kwargs):
		self.set_coord(coords[0], **kwargs)

class rotator(cynematic_unit_one_axis):
	def sensivity(self):
		"""Возвращает тензор производной по положению
		в собственной системе координат в формате (w, v)"""
		return (pyservoce.vector3(), axmul)

	def set_coord(self, coord):
		self.coord = coord
		self.output.relocate(pyservoce.rotate(self.ax, coord * self.mul), **kwargs)

class actuator(cynematic_unit_one_axis):
	def sensivity(self):
		"""Возвращает тензор производной по положению
		в собственной системе координат в формате (w, v)"""
		return (axmul, pyservoce.vector3())

	def set_coord(self, coord):
		self.coord = coord
		self.output.relocate(pyservoce.translate(self.ax, coord * self.mul), **kwargs)

class planemover(cynematic_unit):
	"""Кинематическое звено с двумя степенями свободы для перемещения
	по плоскости"""

	def __init__(self):
		super().__init__(**kwargs)
		self.x = 0
		self.y = 0

	def senses(self):
		return (
			(pyservoce.vector3(1,0,0), pyservoce.vector3()),
			(pyservoce.vector3(0,1,0), pyservoce.vector3())
		)

	def set_coords(self, coords, **kwargs):
		self.x = coord[0]
		self.y = coord[1]
		self.output.relocate(
			pyservoce.translate(pyservoce.vector3(self.x, self.y, 0)), **kwargs)


class cynematic_chain:
	def __init__(self, finallink, startlink = None):
		self.chain = self.collect_chain(finallink, startlink)
		self.chain = self.simplify_chain(self.chain)
		self.parametered_links = self.collect_parametered()

	def collect_parametered(self):
		ret = []
		for l in self.chain:
			if isinstance(l, cynematic_unit):
				ret.append(l)
		return ret

	def collect_coords(self):
		arr = []
		for l in self.parametered_links:
			arr.append(l.coord)
		return arr

	@staticmethod
	def collect_chain(finallink, startlink = None):
		chain = []
		link = finallink

		while link is not startlink:
			chain.append(link)
			link = link.parent

		return chain

	@staticmethod
	def simplify_chain(chain):
		ret = []
		tmp = None

		for l in chain:
			if isinstance(l, cynematic_unit):
				if tmp is not None:
					ret.append(tmp)
				ret.append(l)
			else:
				if tmp is None:
					tmp = l.location
				else:
					tmp = l.location * tmp

		return ret

	def getchain(self):
		return self.chain

	def sensivity(self, coords=None):
		#if coords:
		#	coords = coords.reversed()
		#else:
		#	coords = self.collect_coords()
		
		trsf = pyservoce.nulltrans()
		senses = []

		i = 0
		lit = iter(self.chain)

		while True:
			link = lit.current()
			if isinstance(link, pyservoce.libservoce.transformation):
				trsf = link * trsf
			else:
				sens = link.sensivity()

				radius = trsf.translation()
				wsens = sens[0]
				vsens = (radius, wsens) + sens[1]

				senses.append((wsens, vsens))

				trsf = link.location * trsf

			i+=1
