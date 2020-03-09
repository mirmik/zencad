#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m = cone(r1=10, r2=5, h=10)
m = offset(m, 2)

disp(m)
show()