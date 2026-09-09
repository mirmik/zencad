#!/usr/bin/env python3
"""Typed ShapeList selectors feeding modeling operations."""
from zencad import *



context = Context.deferred(cache=False)
with using_context(context):
    body = box(20, 20, 30, center="xy")
    vertical_edges = body.edges().filter_by(Axis.Z)
    side_faces = body.faces().planar().normal_to(Axis.X)
    top_face = body.faces().planar().sort_by(Axis.Z)[-1]
    rounded = fillet(body, 2, vertical_edges).left(15)
    tapered = draft(body, side_faces, 0.05).right(15)

display(rounded, color=green)
display(tapered, color=yellow)
display(top_face.up(0.01), color=red)
show()
