#from zencad.zenlib import boolops_union as union
#from zencad.zenlib import boolops_difference as difference
#from zencad.zenlib import boolops_intersect as intersect#

def union(arr):
	m = arr[0]
	for a in arr[1:]:
		m = m + a
	return m

def difference(arr):
	m = arr[0]
	for a in arr[1:]:
		m = m - a
	return m

def intersect(arr):
	m = arr[0]
	for a in arr[1:]:
		m = m ^ a
	return m