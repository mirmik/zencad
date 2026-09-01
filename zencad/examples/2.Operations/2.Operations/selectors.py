#!/usr/bin/env python3
"""Typed ShapeList selectors feeding modeling operations."""

import zencad
from zencad import _typed as cad


context = cad.Context.deferred(cache=False)
with cad.using_context(context):
    body = cad.box(20, 20, 30, center="xy")
    vertical_edges = body.edges().filter_by(cad.Axis.Z)
    side_faces = body.faces().planar().normal_to(cad.Axis.X)
    top_face = body.faces().planar().sort_by(cad.Axis.Z)[-1]
    rounded = cad.fillet(body, 2, vertical_edges).left(15)
    tapered = cad.draft(body, side_faces, 0.05).right(15)

# The current public viewer consumes legacy Shape wrappers; native() is the
# explicit owned-snapshot boundary of the private typed API.
zencad.display(zencad.Shape(rounded.native()), color=zencad.green)
zencad.display(zencad.Shape(tapered.native()), color=zencad.yellow)
zencad.display(zencad.Shape(top_face.up(0.01).native()), color=zencad.red)
zencad.show()
