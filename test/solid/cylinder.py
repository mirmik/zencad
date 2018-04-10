#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
m = zencad.cylinder(10, 20)

zencad.display(m)
zencad.show()