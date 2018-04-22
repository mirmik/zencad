#from zencad.zenlib import boolops_union as union
#from zencad.zenlib import boolops_difference as difference
#from zencad.zenlib import boolops_intersect as intersect#

def union(arr):
	if len(arr) == 1: return arr[0]
	narr = []
	for i in range(0, len(arr) // 2):
		narr.append(arr[i] + arr[-i-1])
	if len(arr) % 2 == 1:
		narr.append(arr[len(arr)//2])
	return union(narr)


	#m = arr[0]
	#for a in arr[1:]:
	#	m = m + a
	#return m

def difference(arr):
	m = arr[0]
	for a in arr[1:]:
		m = m - a
	return m

def intersect(arr):
	print("TODO!!!!")
	sys.exit(-1)
	#m = arr[0]
	#for a in arr[1:]:
	#	m = m ^ a
	#return m