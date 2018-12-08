import runpy
import math

import pyservoce

def execfile(path):
	#with open(path) as f:
	#	code = compile(f.read(), path, 'exec')
	#	exec(code, globals(), locals())
	#	return locals()
	file_globals = runpy.run_path(path)
	return file_globals

def deg(grad): 
	return float(grad) / 180.0 * math.pi

def angle_pair(arg):
	if isinstance(arg, tuple) or isinstance(arg, list):
		return arg
	return (0, arg)

def point3(*arg):
	if isinstance(arg[0], pyservoce.point3):
		return arg[0]

	return pyservoce.point3(*arg)

def vector3(*arg):
	if isinstance(arg[0], pyservoce.vector3):
		return arg[0]

	return pyservoce.vector3(*arg)

def points(tpls):
	return [ point3(t) for t in tpls ]

def vectors(tpls):
	return [ vector3(t) for t in tpls ]