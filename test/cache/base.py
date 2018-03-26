#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad.solid as solid
from zencad.widget import *
import math

import zencad.cache
zencad.cache.enable("cache")

m = solid.box(10,10,10)

display(m)
show() 