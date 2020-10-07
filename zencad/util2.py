import zencad.lazifier
import numpy
import pyservoce

@zencad.lazifier.lazy
def numpy_highmap(arr):
	#result = numpy.ndarray((arr.shape[0], arr.shape[1]), dtype=pyservoce.point3)
	result = numpy.ndarray(arr.shape, dtype=pyservoce.point3)

	for i in range(arr.shape[0]):
		for j in range(arr.shape[1]):
			result[i,j] = pyservoce.point3(i,j,arr[i,j])

	return result		

@zencad.lazifier.lazy.lazy(cls=zencad.lazifier.shape_generator)
def restore_shapetype(shp):
	if len(shp.solids()) == 1:
		return shp.solids()[0]

	if len(shp.shells()) == 1:
		return shp.shells()[0]

	elif len(shp.faces()) == 1:
		return shp.faces()[0]

	elif len(shp.wires()) == 1:
		return shp.wires()[0]

	elif len(shp.edges()) == 1:
		return shp.edges()[0]

	else:
		raise Exception("type is not supported: {}".format(shp.shapetype()))
