#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad

m0 = zencad.box(size = [20, 20, 10], center = True)
m1 = zencad.box(size = 20, center = True)
m2 = zencad.box(size = 20)

zencad.display(m0)
zencad.display(m1.right(30))
zencad.display(m2.left(30))
zencad.show()