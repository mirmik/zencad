#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import dzencad.solid as solid
import dzencad.boolops as boolops

import dzencad.trans as trans

import dzencad.widget
import dzencad.stl as stl

m1 = solid.box(20, 20, 40) 
m2 = solid.sphere(20).up(10)
#m3 = boolops.union(m1,m2)

m3 = m1 ^ m2

#trans.translate(3,6,7)

#stl.make_stl("stl.stl", m3)

dzencad.widget.display(m1+m2)
dzencad.widget.display(m3.right(200))
dzencad.widget.show()