#!/usr/bin/env python3
"""ZenCad API example: deterministic split and ordered plane slice."""

import zencad


body = zencad.box(30, 20, 12)
parts = zencad.split(
    body,
    (zencad.infplane().up(4), zencad.infplane().up(8)),
)
colors = (zencad.red, zencad.green, zencad.blue)
for part, part_color in zip(parts, colors):
    zencad.display(part, color=part_color)

lower, upper = zencad.slice(zencad.box(20, center=True).right(40), z=0)
zencad.display(lower, color=zencad.yellow)
zencad.display(upper, color=zencad.magenta)

zencad.show()
