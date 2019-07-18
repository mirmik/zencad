import zencad.controllers
import pyservoce

class cynematic_chain:
	def __init__(self, finallink, startlink = None):
		self.chain = self.collect_chain(finallink, startlink)
		self.chain = self.simplify_chain(self.chain)
		self.parametered_links = self.collect_parametered()

	def collect_parametered(self):
		ret = []
		for l in self.chain:
			if isinstance(l, zencad.controllers.CynematicUnit):
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
			if isinstance(l, zencad.controllers.CynematicUnit):
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
