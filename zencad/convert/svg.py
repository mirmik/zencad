#!/usr/bin/env python3

import svgwrite

class SvgWriter:
	def __init__(self):
		self.draw =  svgwrite.Drawing()

	def begin(self):
		pass

	def save(self):
		self.draw.save()

	def add_edge_to_path(self):
		pass

	def push_edge(self, edge):
		pass

	def push_wire(self, wire, fill=False):
		pass

	def push_face(self, face):
		wire = face.wires()[0]
		self.push_wire(wire, fill=True)


	def push_shape(self, shp):
		print(shp.curvetype())

		if shp.shapetype() == "face":
			self.push_face(shp)

		elif shp.shapetype() == "edge":
			self.push_edge(shp)

		elif shp.shapetype() == "wire":
			self.push_wire(shp)


def shape_to_svg_string(shape):
	writer = SvgWriter()

	writer.begin()
	writer.push_shape(shape)

	return writer.draw.tostring()


if __name__ == "__main__":
	import zencad

	segm = zencad.segment((0,10),(10,0))
	circ = zencad.circle(10, wire=True)

	print(shape_to_svg_string(segm))