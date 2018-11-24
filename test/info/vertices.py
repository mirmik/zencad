#!/usr/bin/env python3

import zencad
from zencad import *

zencad.lazy.diag = True
zencad.lazy.diag_values = True

m = box(10,10,10)

test = [
	point3(0.000000,0.000000,0.000000), 
	point3(0.000000,0.000000,10.000000), 
	point3(0.000000,10.000000,0.000000), 
	point3(0.000000,10.000000,10.000000), 
	point3(10.000000,0.000000,0.000000), 
	point3(10.000000,0.000000,10.000000), 
	point3(10.000000,10.000000,0.000000), 
	point3(10.000000,10.000000,10.000000)
]

print(test == m.vertices().unlazy())

print(test)
print(m.vertices().unlazy())
