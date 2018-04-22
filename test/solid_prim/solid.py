#!/usr/bin/python3
#coding: utf-8

import zencad

zencad.enable_cache(".cache")

m0 = zencad.box(size = 10, center = True)
m1 = zencad.sphere(5)
m2 = zencad.torus(5, 2)
m3 = zencad.cylinder(5, 10, center = True)
m4 = zencad.cone(5, 10, 10)

m5 = zencad.box(10,10,10) + zencad.sphere(5)

zencad.display(m0)
zencad.display(m1.right(20))
zencad.display(m2.right(40))
zencad.display(m3.right(60))
zencad.display(m4.right(80))
zencad.display(m5.right(100))

zencad.show()