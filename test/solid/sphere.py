#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
m = zencad.sphere(10)

zencad.display(m)
zencad.show()