#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import dzencad.solid as solid
from dzencad.widget import *
import dzencad.cache
import math

m = solid.load("temporary.bin")

display(m)
show()