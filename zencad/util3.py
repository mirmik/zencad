import math

def as_indexed(arg):
	if len(arg) != 1:
		return tuple(arg)
	return arg

def deg(grad):
	return float(grad) / 180.0 * math.pi

def deg2rad(d):
	return deg(d)

def rad2deg(d):
	return float(d) * 180.0 / math.pi