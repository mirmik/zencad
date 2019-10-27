import zencad.assemble
import pyservoce

from abc import ABC, abstractmethod

class kinematic_unit(ABC, zencad.assemble.unit):
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

		Для kinematic_unit метод link переопределяется,
		с тем, чтобы линковка происходила не ко входной, 
		а к выходной СК"""

		self.output.link(arg)


class kinematic_unit_one_axis(kinematic_unit):
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
		return (self.sensivity(),)

	#override
	def set_coords(self, coords, **kwargs):
		self.set_coord(coords[0], **kwargs)

	@abstractmethod
	def sensivity(self):
		raise NotImplementedError

	@abstractmethod
	def set_coord(self, coord, **kwargs):
		raise NotImplementedError


class rotator(kinematic_unit_one_axis):
	def sensivity(self):
		"""Возвращает тензор производной по положению
		в собственной системе координат в формате (w, v)"""
		return (self.axmul, pyservoce.vector3())

	def set_coord(self, coord, **kwargs):
		self.coord = coord
		self.output.relocate(pyservoce.rotate(self.ax, coord * self.mul), **kwargs)


class actuator(kinematic_unit_one_axis):
	def sensivity(self):
		"""Возвращает тензор производной по положению
		в собственной системе координат в формате (w, v)"""
		return (pyservoce.vector3(), self.axmul)

	def set_coord(self, coord, **kwargs):
		self.coord = coord
		self.output.relocate(pyservoce.translate(self.ax * coord * self.mul), **kwargs)


class planemover(kinematic_unit):
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


class spherical_rotator(kinematic_unit):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._yaw = 0
		self._pitch = 0

	def senses(self):
		raise NotImplementedError
		#return (
		#	(pyservoce.vector3(1,0,0), pyservoce.vector3()),
		#	(pyservoce.vector3(0,1,0), pyservoce.vector3())
		#)

	def set_yaw(self, angle, **kwargs):
		self._yaw = angle
		self.update_position(**kwargs)

	def set_pitch(self, angle, **kwargs):
		self._pitch = angle
		self.update_position(**kwargs)

	def set_coords(self, coords, **kwargs):
		self._yaw = coord[0]
		self._pitch = coord[1]
		self.update_position(**kwargs)

	def update_position(self, **kwargs):
		self.output.relocate(pyservoce.rotateZ(self._yaw) * pyservoce.rotateY(self._pitch))

class kinematic_chain:
	"""Объект-алгоритм управления участком кинематической чепи от точки
	выхода, до точки входа.

	Порядок следования обратный, потому что звено может иметь одного родителя,
	но много потомков. Цепочка собирается по родителю.

	finallink - конечное звено.
	startlink - начальное звено. 
		Если не указано, алгоритм проходит до абсолютной СК"""

	def __init__(self, finallink, startlink = None):
		self.chain = self.collect_chain(finallink, startlink)
		self.simplified_chain = self.simplify_chain(self.chain)
		self.kinematic_pairs = self.collect_kinematic_pairs()

	def collect_kinematic_pairs(self):
		par = []
		for l in self.chain:
			if isinstance(l, kinematic_unit):
				par.append(l)
		return par

	#def collect_coords(self):
	#	arr = []
	#	for l in self.parametered_links:
	#		arr.append(l.coord)
	#	return arr

	@staticmethod
	def collect_chain(finallink, startlink = None):
		chain = []
		link = finallink

		while link is not startlink:
			chain.append(link)
			link = link.parent

		if startlink is not None:
			chain.append(startlink)

		return chain

	@staticmethod
	def simplify_chain(chain):
		ret = []
		tmp = None

		for l in chain:
			if isinstance(l, kinematic_unit):
				if tmp is not None:
					ret.append(tmp)
					tmp = None
				ret.append(l)
			else:
				if tmp is None:
					tmp = l.location
				else:
					tmp = tmp * l.location

		if tmp is not None:
			ret.append(tmp)

		return ret

	def getchain(self):
		return self.chain

	def sensivity(self, basis=None):
		"""Вернуть массив тензоров производных положения выходного
		звена по вектору координат в виде [(w_i, v_i) ...]"""

		trsf = pyservoce.nulltrans()
		senses = []

		outtrans = self.chain[0].global_location

		"""Два разных алгоритма получения масива тензоров чувствительности.
		Первый - проход по цепи с аккумулированием тензора трансформации.
		Второй - по глобальным объектам трансформации

		Возможно следует использовать второй и сразу же перегонять в btrsf вместо outtrans"""

		if False:
			for link in self.simplified_chain:
				if isinstance(link, pyservoce.libservoce.transformation):
					trsf = link * trsf
				
				else:
					lsenses = link.senses()
					radius = trsf.translation()
				
					for sens in reversed(lsenses):
						
						wsens = sens[0]
						vsens = wsens.cross(radius) + sens[1]
				
						itrsf = trsf.inverse()
				
						senses.append((
							itrsf(wsens), 
							itrsf(vsens)
						))
				
					trsf = link.location * trsf

		else:
			for link in self.kinematic_pairs:
				lsenses = link.senses()
				
				linktrans = link.output.global_location
				trsf = linktrans.inverse() * outtrans
			
				radius = trsf.translation()
			
				for sens in reversed(lsenses):
					
					wsens = sens[0]
					vsens = wsens.cross(radius) + sens[1]
				
					itrsf = trsf.inverse()
				
					senses.append((
						itrsf(wsens), 
						itrsf(vsens)
					))

		"""Для удобства интерпретации удобно перегнать выход в интуитивный базис."""
		if basis is not None:
			btrsf = basis.global_location
			#trsf =  btrsf * outtrans.inverse()
			#trsf =  outtrans * btrsf.inverse() #ok
			trsf =  btrsf.inverse() * outtrans #ok
			#trsf =  outtrans.inverse() * btrsf
			#trsf =  trsf.inverse()

			senses = [ (trsf(w), trsf(v)) for w, v in senses ]

		return list(reversed(senses))
