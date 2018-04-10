#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
m0 = zencad.cone(r1 = 10, r2 = 0, h = 20)
m1 = zencad.cone(r1 = 10, r2 = 20, h = 20, center = True)

zencad.display(m0)
zencad.display(m1.right(30))
zencad.show()