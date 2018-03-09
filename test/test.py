#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import dzencad.solid as solid
import dzencad.boolops as boolops

import dzencad.widget
import dzencad.stl as stl

m1 = solid.box(20, 20, 40) 
m2 = solid.sphere(20)
m3 = boolops.union(m1,m2)

stl.make_stl("stl.stl", m3)

dzencad.widget.display(m3)
dzencad.widget.show()