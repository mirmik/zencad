import pyservoce
from zencad.lazifier import lazy, shape_generator
import zencad.transform

@lazy.lazy(cls=shape_generator)
def union(arr):
    return pyservoce.union(arr)


@lazy.lazy(cls=shape_generator)
def difference(arr):
    return pyservoce.difference(arr)


@lazy.lazy(cls=shape_generator)
def intersect(arr):
    return pyservoce.intersect(arr)


@lazy.lazy(cls=shape_generator)
def section(a, b=0):
	"""
		Make section between 'a' and 'b'.
		Oposite the intersect, which finds the intersection of bodies, 
		the section finds the intersection of the shells of bodies.

		Arguments:
		a, b - is pair of algorithm arguments. The algorithm is commutative.
			a and b can be numeric or vector. In that case algorithm find
			section with a given plane.
	"""

	def to_halfspace_if_need(x):
		if isinstance(x, (tuple, list, pyservoce.vector3)):
			vec = pyservoce.vector3(x)
			return (
				zencad.transform.translate(*vec) * 
				zencad.transform.short_rotate(fromvec=(0,0,1), tovec=vec)
			)(pyservoce.halfspace())

		elif isinstance(x, (int, float)):
			return pyservoce.halfspace().up(x)

		return x

	result = pyservoce.section(
			to_halfspace_if_need(a),
			to_halfspace_if_need(b)
		)

	return result