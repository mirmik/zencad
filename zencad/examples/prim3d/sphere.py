#!/usr/bin/env python3
#coding: utf-8

from zencad import *
test_mode()

m1 = sphere(r=10)
m2 = sphere(r=10, an1=deg(135))
m3 = sphere(r=10, an1=deg(10), an2=deg(40))
m4 = sphere(r=10, an1=deg(10), an2=deg(40), an3=deg(135))

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))

show()