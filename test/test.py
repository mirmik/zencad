#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad.solid as solid

m1 = solid.box(10,10,10)
m2 = solid.box(10,10,9)

print(m1.hash1())
print(m2.hash1())
print(m1.hash2())
print(m2.hash2())
