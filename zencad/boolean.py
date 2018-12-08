import pyservoce
from zencad.lazy import lazy

@lazy
def union(arr): 
	return pyservoce.union(arr)

@lazy
def difference(arr): return pyservoce.difference(arr)

@lazy
def intersect(arr): return pyservoce.intersect(arr)