# Based on Platonic Solids for OpenScad - v0.7 

import math

Cepsilon = 0.00000001;

# Function: clean
#
# Parameters:
#	n - A number that might be very close to zero
# Description:  
#	There are times when you want a very small number to 
# 	just be zero, instead of being that very small number.
#	This function will compare the number to an arbitrarily small 
#	number.  If it is smaller than the 'epsilon', then zero will be 
# 	returned.  Otherwise, the original number will be returned.
#
def clean(n):
	if n < 0:
		if n < -Cepsilon:
			return n 
		else: 
			return 0 
	else:
		if n < Cepsilon:
			return 0
		else:
			return n 

# Convert from cartesian to spherical
def sph(long, lat, rad=1):
	return [long, lat, rad]

# Convert spherical to cartesian
def sph_to_cart(s):
	return [
		clean(s[2] * math.sin(s[1]) * math.cos(s[0])),  
		clean(s[2] * math.sin(s[1]) * math.sin(s[0])),
		clean(s[2] * math.cos(s[1]))
	]

# Convert from cartesian to spherical
def sph_from_cart(c):
	return sph(
		math.atan2(c[1],c[0]), 
		math.atan2(math.sqrt(c[0]*c[0]+c[1]*c[1]), c[2]), 
		math.sqrt(c[0]*c[0]+c[1]*c[1]+c[2]*c[2])
	)

def sphu_from_cart(c, rad=1):
	return sph(
		math.atan2(c[1],c[0]), 
		math.atan2(math.sqrt(c[0]*c[0]+c[1]*c[1]), c[2]), 
		rad
	)

# compute the chord distance between two points on a sphere
def sph_dist(c1, c2):
	return math.sqrt(
			c1[2]*c1[2] 
			+ c2[2]*c2[2] 
			- 2*c1[2]*c2[2] * (
				(math.cos(c1[1])*math.cos(c2[1])) 
				+ math.cos(c1[0]-c2[0])*math.sin(c1[1])*math.sin(c2[1])
				)   
	)

tetra_cart = [
	[+1, +1, +1],
	[-1, -1, +1],
	[-1, +1, -1],
	[+1, -1, -1]
];

def tetra_unit(rad=1):
	return [
		sph_to_cart(sphu_from_cart(tetra_cart[0], rad)), 
		sph_to_cart(sphu_from_cart(tetra_cart[1], rad)),
		sph_to_cart(sphu_from_cart(tetra_cart[2], rad)),
		sph_to_cart(sphu_from_cart(tetra_cart[3], rad)),
	]


tetrafaces = [
	[0,3,1],
	[0,1,2],
	[2,1,3],
	[0,2,3]
];

tetra_edges = [
	[0,1],
	[0,2],
	[0,3], 
	[1,2], 
	[1,3], 
	[2,3],	
	];

def tetrahedron(rad=1): return [tetra_unit(rad), tetrafaces, tetra_edges];
