#!/usr/bin/env python3
#coding: utf-8

import zencad
import zencad.solid as solid
from zencad.widget import *

zencad.enable_cache(".cache")

#box = solid.box(300, 200, 100, center = True).up(100)
sphere = solid.sphere(100).up(100)

#union = box + sphere

#display(box)
display(sphere)

#display(union)
show()