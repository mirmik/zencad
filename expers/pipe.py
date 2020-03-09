#!/usr/bin/env python3
"""
ZenCad API example: revol2
"""

from zencad import *
import zencad.internal_models

#profile = box(10, center=True).shells()[0]
profile = (box(12) - box(12, center=True)).shells()[0]
spine = interpolate([(0,0,0), (0,0,10), (20,0,40)], tangs=[(0,0,1), (0,0,0), (0,0,0)])

m = pipe(profile, spine)

disp(m)
show()