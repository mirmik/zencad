import zencad.assemble
import pyservoce

from abc import ABC, abstractmethod

from zencad.assemble import kinematic_unit

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
