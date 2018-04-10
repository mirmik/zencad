#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
m = zencad.torus(r1 = 10, r2 = 3)

zencad.display(m)
zencad.show()