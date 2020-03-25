#!/usr/bin/env python3


class SvgWriter:
	def __init__(self):
		pass

	def add_edge_to_path(self):
		pass

	def push_wire(self, wire):
		pass

	def push_shape(self, shp):
		print(shp.curvetype())

		if shp.shapetype() == "face":
			wire = shp.wires()[0]


		elif shp.shapetype() == "edge":
			if shp.curvetype() == "line":
				a, b = shp.endpoints()
				a, b = a[:2], b[:2]
				self.push_segment(a,b)







if __name__ == "__main__":
	import zencad

	segm = zencad.segment((0,10),(10,0))
	circ = zencad.circle(10, wire=True)

	shape_to_svg("test0.svg", segm)
	shape_to_svg("test1.svg", circ)