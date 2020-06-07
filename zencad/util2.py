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