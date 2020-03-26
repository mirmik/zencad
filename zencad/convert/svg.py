#!/usr/bin/env python3

import svgwrite
import evalcache
import math

def color_convert(zclr):
	r,g,b,a = zclr.r, zclr.g, zclr.b, zclr.a
	r,g,b,a = ( x * 100 for x in (r,g,b,a))
	return svgwrite.rgb(r,g,b,'%')

def box_size(shape, mapping):
	box = shape.bbox()

	if mapping:
		off = (-box.xmin, -box.ymin)
	else:
		off = (0,0)

	return (
		str(box.xmax - box.xmin),
		str(box.ymax - box.ymin),
	), off
	

class SvgWriter:
	def __init__(self, fpath = None, size=None, off=None, **extras):
		if fpath is None:
			self.dwg =  svgwrite.Drawing(size=size, **extras)
		else:
			self.dwg =  svgwrite.Drawing(fpath, size=size, **extras)

		self.off_x = off[0]
		self.off_y = off[1]

	def proj(self, pnt):
		epsillon = 1e-5
		if abs(pnt.z) > epsillon:
			raise Exception("z coord is not zero") 
		return pnt.x + self.off_x, pnt.y + self.off_y

	def begin(self):
		pass

	def save(self):
		self.dwg.save()

	def add_edge_to_path(self):
		pass

	def push_edge(self, edge):
		self.push_wire(edge)

	def push_wire(self, wire):
		print("push_wire")
		print(wire.edges())
		if wire.shapetype() == "wire":
			edges = wire.edges()
		else:
			edges = [wire]

		if len(edges) > 1:
			edges = zencad.wire_edges_orientation(edges)
		else:
			edges = [( edges[0], False )]

		edges = list(edges)
		print(edges)

		strt = edges[0][0].endpoints()[1 if edges[0][1] else 0]
		strt = self.proj(strt) 

		self.path.push(f"M {strt[0]} {strt[1]}")
		for e in edges:
			rev = e[1]
			e = e[0] 

			s, f = e.endpoints()
			s, f = self.proj(s), self.proj(f)

			if rev:
				s, f = f, s

			if e.curvetype() == "line":
				self.path.push(f"L {f[0]} {f[1]}")

			elif e.curvetype() == "circle":
				angle = e.range()[1] - e.range()[0]
				c,r,x,y = e.circle_parameters()

				c = self.proj(c)
				
				if (abs(angle - math.pi * 2) < 1e-5):
					d = (f[0] - c[0], f[1] - c[1])
					self.path.push(f"A {r} {r} {0} {0} {0} {c[0] - d[0]} {c[1] - d[1]}")
					self.path.push(f"A {r} {r} {0} {0} {0} {f[0]} {f[1]}")

				else:
					large_arc = 1 if angle > math.pi else 0
					sweep = 1 if (x.cross(y)).z > 0 else 0
					self.path.push(f"A {r} {r} {0} {large_arc} {sweep} {f[0]} {f[1]}")

			else: 
				raise Exception(f"svg:wire : curvetype is not supported: {e.curvetype()} ")

		closed=True
		if closed:
			self.path.push("Z")

	def push_face(self, face):
		print("push_face")

		for w in face.wires():
			self.push_wire(w)


	def push_shape(self, shp, color):
		shp = zencad.restore_shapetype(shp)

		if shp.shapetype() == "face":
			fill_opacity = 1
			self.path = self.dwg.path(stroke="", fill=color, fill_opacity=1)
			self.push_face(shp)

		elif shp.shapetype() == "edge":
			self.path = self.dwg.path(stroke=color, fill="", fill_opacity=0)
			self.push_edge(shp)

		elif shp.shapetype() == "wire":
			self.path = self.dwg.path(stroke=color, fill="", fill_opacity=0)
			self.push_wire(shp)

		else:
			raise Exception(f"shapetype is not supported: {shp.shapetype()} ")


		self.dwg.add(self.path)
	


def shape_to_svg(fpath, shape, color, mapping):
	shape = evalcache.unlazy_if_need(shape)
	color = color_convert(color)
	size, off = box_size(shape, mapping)
	writer = SvgWriter(fpath=fpath, off=off, size=size)

	writer.begin()
	writer.push_shape(shape, color=color)

	writer.save()


def shape_to_svg_string(shape, color, mapping):
	shape = evalcache.unlazy_if_need(shape)
	color = color_convert(color)
	size, off = box_size(shape,mapping)
	writer = SvgWriter(size=size, off=off)

	writer.begin()
	writer.push_shape(shape, color=color)

	return writer.dwg.tostring()


if __name__ == "__main__":
	import zencad

	shp = zencad.unify(
		zencad.rectangle(10,20) 
		+ zencad.rectangle(10,20,center=True)
		+ zencad.circle(r=10)
		#- zencad.rectangle(2)
		-zencad.circle(5)
	)
	clr = zencad.color(0.5,0,0.5)

	mapping = True

	zencad.disp(shp)
	zencad.show()

	print(shape_to_svg_string(shp, color=clr, mapping=mapping))
	shape_to_svg("test.svg", shp, color=clr, mapping=mapping)