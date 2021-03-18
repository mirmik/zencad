#!/usr/bin/env python3
"""
ZenCad API example: pipe_shell
"""

from zencad import *

a = circle(r=20)
b = circle(r=10).up(10)

proto_wires = [
    circle(10,     wire=True),
    ellipse(10, 16, wire=True),
    ellipse(10, 20, wire=True),
    ellipse(10, 13, wire=True),
    circle(10,     wire=True)
]

spine = interpolate(
    [(0, 0, 0), (40, 0, 50), (80, 0, 100)],
    tangs=[(0, 0, 1), None, (0, 0, 1)])

uniform = spine.uniform(len(proto_wires))

wires = [
    (move(*spine.d0(uniform[i])) * short_rotate((0, 0, 1), spine.d1(uniform[i])))(
        p) for i, p in enumerate(proto_wires)]

m0 = pipe_shell(wires, spine, solid=True)
m1 = pipe_shell(wires, spine, solid=False)

disp(wires, color.red)
disp(spine, color.red)
disp([w.forw(50) for w in wires], color.red)

disp(m0.forw(50))
disp(m1.forw(100))

show()
