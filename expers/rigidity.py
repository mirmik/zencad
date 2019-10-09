#!/usr/bin/env python3

import zencad
import zencad.libs.rigidity

import numpy

#E = 200000 * 10**6
#G = 82 * 10**9
E = 2000 * 10**6
G = 10 * 10**9

F = 1
Jx = 1
Jy = 1
Jz = 1
l = 1

X1 = 0
Y1 = 0
Z1 = 0
Q1 = 0
R1 = 1
S1 = 0

#X2 = 0
#Y2 = 0
#Z2 = -1
#Q2 = 0
#R2 = 0
#S2 = 0

ridmat = zencad.libs.rigidity.rigidity_matrix_part(E, G, F, Jx, Jy, Jz, l)
invridmat = numpy.linalg.inv(ridmat)
flexmat = zencad.libs.rigidity.flexibility_matrix_part(E, G, F, Jx, Jy, Jz, l)

#print(ridmat)
#print(invridmat)
#force = numpy.array([X1,Y1,Z1,Q1,R1,S1,X2,Y2,Z2,Q2,R2,S2])
force = numpy.array([X1,Y1,Z1,Q1,R1,S1])

ret = flexmat.dot(force)

print("x:", ret[0,0])
print("y:", ret[0,1])
print("z:", ret[0,2])
print("q:", ret[0,3])
print("r:", ret[0,4])
print("s:", ret[0,5])
print()

ret = invridmat.dot(force)

print("x:", ret[0,0])
print("y:", ret[0,1])
print("z:", ret[0,2])
print("q:", ret[0,3])
print("r:", ret[0,4])
print("s:", ret[0,5])

#ret = flexmat.dot(force)
#
#print("x1:", ret[0,0])
#print("y1:", ret[0,1])
#print("z1:", ret[0,2])
#print("q1:", ret[0,3])
#print("r1:", ret[0,4])
#print("s1:", ret[0,5])
#print()
#print("x2:", ret[0,6])
#print("y2:", ret[0,7])
#print("z2:", ret[0,8])
#print("q2:", ret[0,9])
#print("r2:", ret[0,10])
#print("s2:", ret[0,11])
#print()
#
#ret = invridmat.dot(force)
#
#print("x1:", ret[0,0])
#print("y1:", ret[0,1])
#print("z1:", ret[0,2])
#print("q1:", ret[0,3])
#print("r1:", ret[0,4])
#print("s1:", ret[0,5])
#print()
#print("x2:", ret[0,6])
#print("y2:", ret[0,7])
#print("z2:", ret[0,8])
#print("q2:", ret[0,9])
#print("r2:", ret[0,10])
#print("s2:", ret[0,11])#