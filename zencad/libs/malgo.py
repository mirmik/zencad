import zencad
import math
import numpy
import time


def kinematic_backpack(senses, target, current):
    sens = [s.to_array() for s in senses]
    target = (current.inverse() * target).to_array()
    return zencad.malgo.svd_backpack(target, sens)


def kinematic_backpack_translation_only(senses, target):
    sens = [s.lin for s in senses]
    return zencad.malgo.svd_backpack(target, sens)


def normalize(v):
    n = numpy.linalg.norm(v)
    if n == 0:
        return numpy.zeros(v.size)
    return v / n


def naive_backpack(target, vectors, maxiters=None, koeffs=None, penalty=None, alpha=0.5, epsilon=0.000000001):
    """Наивное решение задачи поиска линейной комбинации методом покоординатного спуска"""

    def sign(x):
        if x >= 0:
            return 1
        else:
            return -1

    target = numpy.array(target)
    vectors = [numpy.array(v) for v in vectors]

    current = numpy.zeros(len(target), dtype=numpy.float64)
    coords = numpy.zeros(len(vectors), dtype=numpy.float64)

    tgtnorm = numpy.linalg.norm(target)
    vnormalized = [normalize(v) for v in vectors]
    vnorms = [numpy.linalg.norm(v) for v in vectors]

    iterations = 0
    while True:
        iterations += 1
        delta = target - current

        if numpy.linalg.norm(delta) < epsilon:
            break

        for i in range(len(vectors)):
            curcoord = vnormalized[i].dot(delta) * alpha / vnorms[i]

            if koeffs:
                curcoord *= koeffs[i]

            if penalty and penalty[i] != 0:
                if sign(curcoord) == penalty[i]:
                    curcoord = curcoord * 0

            coords[i] += curcoord
            current += vectors[i] * curcoord

        if maxiters is not None:
            if iterations == maxiters:
                break

    return coords, iterations


def grad_backpack(target, vectors, maxiters=None, koeffs=None, penalty=None, alpha=0.5, epsilon=0.000000001):
    """Наивное решение задачи поиска линейной комбинации методом покоординатного спуска"""

    def sign(x):
        if x >= 0:
            return 1
        else:
            return -1

    target = numpy.array(target)
    vectors = [numpy.array(v) for v in vectors]

    current = numpy.zeros(len(target), dtype=numpy.float64)
    coords = numpy.zeros(len(vectors), dtype=numpy.float64)

    tgtnorm = numpy.linalg.norm(target)
    vnormalized = [normalize(v) for v in vectors]
    vnorms = [numpy.linalg.norm(v) for v in vectors]

    iterations = 0
    while True:
        iterations += 1
        delta = target - current

        if numpy.linalg.norm(delta) < epsilon:
            break

        koeffs = numpy.array([v.dot(delta) for v in vnormalized])
        koeffs *= 0.5

        for i in range(len(vectors)):
            if vnorms[i] != 0:
                coords[i] += koeffs[i] / vnorms[i]

        # print(coords)

        current = numpy.zeros(len(target))
        for i in range(len(vectors)):
            current += vectors[i] * coords[i]

    return coords, iterations


def fast_backpack(target, vectors):
    """Наивное решение задачи поиска линейной комбинации методом покоординатного спуска"""

    target = numpy.array(target)
    vectors = [numpy.array(v) for v in vectors]
    vectors_normalized = [normalize(v) for v in vectors]
    vectors_norms = [numpy.linalg.norm(v) for v in vectors]

    tgtnorm = numpy.linalg.norm(target)

    coords = numpy.zeros(len(vectors), dtype=numpy.float64)

    for i in range(len(coords)):
        #vnorm = numpy.linalg.norm(vectors_normalized[i])
        coords[i] = target.dot(vectors_normalized[i]) / \
            vectors_norms[i]  # / math.sqrt(tgtnorm * vnorm)

    return coords, 1


def svd_backpack(target, vectors, koeffs=None, penalty=None):
    def sign(x):
        if x >= 0:
            return 1
        else:
            return -1

    target = numpy.array(target)
    start_vectors = vectors
    vectors = [numpy.array(v) for v in vectors]

    if koeffs:
        vectors = [vectors[i] * koeffs[i] for i in range(len(vectors))]

    m = numpy.array(vectors).transpose()
    im = numpy.linalg.pinv(m)

    res = im.dot(target)

    if penalty:
        penaltied = set()
        for i in range(len(vectors)):
            if sign(res[i]) == penalty[i]:
                penaltied.add(i)

        vectors = [vectors[i]
                   for i in range(len(vectors)) if i not in penaltied]

        vectors = [numpy.array(v) for v in vectors]
        m = numpy.array(vectors).transpose()
        im = numpy.linalg.pinv(m)

        res = im.dot(target)

        rres = []
        idx = 0
        for i in range(len(start_vectors)):
            if i in penaltied:
                rres.append(0)
            else:
                rres.append(res[idx])
                idx += 1
    else:
        rres = res

    if koeffs:
        rres = [rres[i] * koeffs[i] for i in range(len(rres))]

    return rres, 1


# def penalty_backpack(target, vectors, koeffs, penalty, maxiters=None, alpha=1, epsilon=0.0001):
#	"""Наивное решение задачи поиска линейной комбинации методом покоординатного спуска"""
#
#	def sign(x):
#		if x >= 0:
#			return 1
#		else:
#			return -1
#
#	target = numpy.array(target)
#	vectors = [ numpy.array(v) for v in vectors ]
#
#	current = numpy.zeros(len(target), dtype=numpy.float64)
#	coords = numpy.zeros(len(vectors), dtype=numpy.float64)
#
#	tgtnorm = numpy.linalg.norm(target)
#	vnormalized = [normalize(v) for v in vectors ]
#	vnorms = [numpy.linalg.norm(v) for v in vectors ]
#
#	iterations = 0
#	debug = False
#	while True:
#		iterations+=1
#		delta = target - current
#
#		#if debug:
#		#	print(delta, coords)
#
#		if numpy.linalg.norm(delta) < epsilon:
#			break
#
#		for i in range(len(vectors)):
#			curcoord = vnormalized[i].dot(delta) * alpha / vnorms[i]
#
#			if i == 0:
#				curcoord *= 1
#
#			#if debug:
#			#	print(i, curcoord)
#
#			#if debug:
#			#	print("penalty", penalty)
#			#	print("ndelta", i, curcoord)
#
#			if penalty[i] != 0:
#				if sign(curcoord) == penalty[i]:
#					curcoord = curcoord * 0
#
#			coords[i] += curcoord
#			current += vectors[i] * curcoord
#			delta = target - current
#
#			#if debug:
#			#	print(coords)
#
#		if maxiters is not None:
#			if maxiters == iterations:
#				break
#
#	return coords, iterations
