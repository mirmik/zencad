#!/usr/bin/env python3
#coding: utf-8

import zencad

m = zencad.ngon(r = 10, n = 6).fillet(1, list([0,1,2,3,4,5]))
zencad.display(m)

zencad.show()