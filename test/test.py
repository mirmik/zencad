#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad.solid as solid
import zencad.boolops as boolops

import zencad.trans as trans

import zencad.widget
import zencad.stl as stl

m1 = solid.box(20, 20, 40) 
m2 = solid.sphere(20).up(10)
#m3 = boolops.union(m1,m2)


#trans.translate(3,6,7)

#stl.make_stl("stl.stl", m3)

zencad.widget.display(m1)
#zencad.widget.display(m3.right(200))
zencad.widget.show()