#!/usr/bin/env python3




def shape_to_svg(file, shp):
	print(shp.curvetype())


	if shp.curvetype() == line:
		a, b = shp.curve_parameters()



















if __name__ == "__main__":
	import zencad

	segm = zencad.segment((0,10),(10,0))
	circ = zencad.circle(10, wire=True)

	shape_to_svg("test.svg", segm)
	shape_to_svg("test.svg", circ)