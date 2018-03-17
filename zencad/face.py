from zencad.zenlib import face_polygon as polygon
from zencad.zenlib import face_circle as circle

import math
import zencad.math3
from zencad import error

def ngon(n, rad = None, a = None):
	if a == None and rad == None:
		zencad.error("ngon args error")

	angles = [2*math.pi / n * i for i in range(0, n)]

	if a != None:
		rad = a / 2 / math.sin(math.pi/n)

	pnts = zencad.math3.points((rad*math.cos(a), rad*math.sin(a)) for a in angles)
	return polygon(pnts)	



	

def square(a, center = False):
	if center:
		return ngon(n = 4, a = a)