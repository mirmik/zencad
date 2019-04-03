#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

NMin = 3
NMax = 12

marr = [ngon(r=10, n=i) for i in range(NMin, NMax + 1)]
for i in range(0, len(marr)):
    display(marr[i].right(i * 30))

show()
