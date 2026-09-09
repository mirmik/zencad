#!/usr/bin/env python3
"""ZenCad API example: positive and negative face draft."""

import zencad


body = zencad.box(20, center="xy")
side_faces = body.faces().filter_by_position(zencad.Axis.Z, 10)
positive = zencad.draft(body, side_faces, zencad.deg(5)).left(25)
negative = zencad.draft(body, side_faces, zencad.deg(-5)).right(25)

zencad.display(positive, color=zencad.green)
zencad.display(negative, color=zencad.yellow)
zencad.show()
