import zencad
import numpy
import time

def normalize(v):
	return v / numpy.linalg.norm(v)

def naive_backpack(target, vectors, alpha=0.95, epsilon=0.000000001):
	"""Наивное решение задачи поиска линейной комбинации путём покоординатного спуска"""

	target = numpy.array(target)
	vectors = [ numpy.array(v) for v in vectors ]

	current = numpy.zeros(len(target), dtype=numpy.float64)
	coords = numpy.zeros(len(vectors), dtype=numpy.float64)

	tgtnorm = numpy.linalg.norm(target)
	vnormalized = [normalize(v) for v in vectors ]
	vnorms = [numpy.linalg.norm(v) for v in vectors ]

	iterations = 0
	while True:
		iterations+=1
		delta = target - current

		if numpy.linalg.norm(delta) < epsilon:
			break
		
		for i in range(len(vectors)):
			curcoord = vnormalized[i].dot(delta) * alpha / vnorms[i]
			coords[i] += curcoord
			current += vectors[i] * curcoord

	return coords, iterations


