#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad

m = zencad.segment(zencad.point(0,0,0), zencad.point(10,20,30))
zencad.display(m)

zencad.show()