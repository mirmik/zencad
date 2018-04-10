#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
m0 = zencad.cylinder(r = 10, h = 20)

zencad.display(m0)
zencad.show()