#!/usr/bin/env python3
"""
ZenCad API example: pipe_shell_frenet
"""

from zencad import *

ps = [(20, 0, 0), (20, 0, 10), (30, 0, 5)]

profile = polysegment(ps, closed=True)
spine = helix(h=100, r=20, step=30)

m0 = pipe_shell([profile], spine, frenet=False)
m1 = pipe_shell([profile], spine, frenet=True, solid=False)
m2 = pipe_shell([profile], spine, frenet=True, solid=True)

disp(m0.right(140), color.red)
disp(m1.right(70))
disp(m2)

show()