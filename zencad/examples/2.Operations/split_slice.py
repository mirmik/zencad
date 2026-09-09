#!/usr/bin/env python3
"""ZenCad API example: deterministic split and ordered plane slice."""
from zencad import *



body = box(30, 20, 12)
parts = split(
    body,
    (infplane().up(4), infplane().up(8)),
)
colors = (red, green, blue)
for part, part_color in zip(parts, colors):
    display(part, color=part_color)

lower, upper = slice(box(20, center=True).right(40), z=0)
display(lower, color=yellow)
display(upper, color=magenta)

show()
