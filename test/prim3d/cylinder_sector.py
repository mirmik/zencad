#!/usr/bin/env python3
#coding: utf-8

import zencad
m0 = zencad.cylinder(r = 10, h = 20, angle = zencad.deg(50))

zencad.display(m0)
zencad.show()