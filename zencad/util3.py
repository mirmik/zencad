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

def angle_pair(arg):
	print("angle_pair")
	if isinstance(arg, tuple) or isinstance(arg, list):
		return arg

	if (arg >= 0):
		return (0, arg)
	else:
		return (arg, 0)
