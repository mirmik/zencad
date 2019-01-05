#!/usr/bin/env python3
#coding: utf-8

import zencad

NMin = 3
NMax = 12

marr = [zencad.ngon(r = 10, n = i) for i in range(NMin, NMax+1)]
for i in range(0, len(marr)): zencad.display(marr[i].right(i*30))

zencad.show()