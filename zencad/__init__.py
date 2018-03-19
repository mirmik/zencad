import math

def gr(rad):
	return rad / 180 * math.pi

def error(str):
	print("ZenCadError: " + str)
	exit(-1)

from zencad.math3 import point as pnt
from zencad.math3 import points
from zencad.zenlib import ZenVertex as vertex