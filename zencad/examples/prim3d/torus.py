#!/usr/bin/env python3
#coding: utf-8

from zencad import *
test_mode()

tor_r1=5
tor_r2=2
tor_u=deg(135)
tor_v1=deg(-90)
tor_v2=deg(180)

m0 = torus(r1=tor_r1, r2=tor_r2)
m1 = torus(r1=tor_r1, r2=tor_r2, uangle=tor_u)
m2 = torus(r1=tor_r1, r2=tor_r2, vangle=(tor_v1,tor_v2))
m3 = torus(r1=tor_r1, r2=tor_r2, vangle=(tor_v1,tor_v2), uangle=tor_u)

display(m0.right(30*0))
display(m1.right(30*1))
display(m2.right(30*2))
display(m3.right(30*3))

show()