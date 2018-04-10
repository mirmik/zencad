#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad

m = zencad.box(size = [20, 20, 10], center = True)
zencad.display(m)

zencad.show()