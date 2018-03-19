from zencad.zenlib import face_polygon as polygon
from zencad.zenlib import face_circle as circle

import math
import zencad.math3
from zencad import pnt
from zencad import error

def ngon(n, rad = None, a = None):
	if a == None and rad == None:
		zencad.error("ngon args error")

	angles = [2*math.pi / n * i for i in range(0, n)]

	if a != None:
		rad = a / 2 / math.sin(math.pi/n)

	pnts = zencad.math3.points((rad*math.cos(a), rad*math.sin(a)) for a in angles)
	return polygon(pnts)	


#def rounded_ngon(rad, n, rrad, nums):
#wire.

#	#def add_segment(last, base):
#	#def add_arc(last, base):
#
#	angles = [2*math.pi / n * i for i in range(0, n)]
#
#	pnts = zencad.math3.points((rad*math.cos(a), rad*math.sin(a)) for a in angles)
#	return polygon(pnts)	


	

def square(a, center = False):
	if center:
		return polygon(
			[
				pnt(-a/2, -a/2),
				pnt(-a/2, +a/2),
				pnt(+a/2, +a/2),
				pnt(+a/2, -a/2),
			],
		)
	else:
		return polygon(
			[
				pnt(0, 0),
				pnt(0, a),
				pnt(a, a),
				pnt(a, 0),
			],
		)

def rectangle(a, b, center = False):
	if center:
		return polygon(
			[
				pnt(-a/2, -b/2),
				pnt(-a/2, +b/2),
				pnt(+a/2, +b/2),
				pnt(+a/2, -b/2),
			],
		)
	else:
		return polygon(
			[
				pnt(0, 0),
				pnt(0, b),
				pnt(a, b),
				pnt(a, 0),
			],
		)