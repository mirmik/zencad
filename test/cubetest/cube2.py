#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad.solid as solid
from zencad.widget import *
import zencad.cache
import math

m = solid.load("temporary.bin")

display(m)
show()