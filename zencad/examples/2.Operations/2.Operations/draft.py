#!/usr/bin/env python3
"""ZenCad API example: positive and negative face draft."""
from zencad import *



body = box(20, center="xy")
side_faces = body.faces().filter_by_position(Axis.Z, 10)
positive = draft(body, side_faces, deg(5)).left(25)
negative = draft(body, side_faces, deg(-5)).right(25)

display(positive, color=green)
display(negative, color=yellow)
show()
