#!/usr/bin/python3
#coding: utf-8

import zencad
m = zencad.cone(r1 = 20, r2 = 10, h = 20, center = True)

zencad.display(m)
zencad.show()