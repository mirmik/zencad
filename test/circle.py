#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

from zencad import *

display(circle(28).face())
display(circle(28).right(40))

f = (circle(28).face() + face.circle(28).right(40)).forw(80)
display(linear_extrude(f, 20))

show()