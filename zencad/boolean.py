import pyservoce
from zencad.lazifier import lazy, shape_generator

@lazy.lazy(cls=shape_generator)
def union(arr): 
	return pyservoce.union(arr)

@lazy.lazy(cls=shape_generator)
def difference(arr): return pyservoce.difference(arr)

@lazy.lazy(cls=shape_generator)
def intersect(arr): return pyservoce.intersect(arr)