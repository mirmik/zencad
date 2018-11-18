import pyservoce
from zencad.lazy import lazy

@lazy
def union(arr): 
	return pyservoce.make_union(arr)

@lazy
def difference(arr): return pyservoce.make_difference(arr)

@lazy
def intersect(arr): return pyservoce.make_intersect(arr)