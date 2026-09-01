#!/usr/bin/env python3
# coding: utf-8

from zencad import *
import math

height = 70
width = 50
thickness = 30

# BASE
pnt1 = point3(-width / 2, 0, 0)
pnt2 = point3(-width / 2, -thickness / 4, 0)
pnt3 = point3(0, -thickness / 2, 0)
pnt4 = point3(width / 2, -thickness / 4, 0)
pnt5 = point3(width / 2, 0, 0)

edge1 = segment(pnt1, pnt2)
edge2 = circle_arc(pnt2, pnt3, pnt4)
edge3 = segment(pnt4, pnt5)

wire = sew([edge1, edge2, edge3])
profile = sew([wire, wire.mirrorX()])
body = profile.fill().extrude(height)
body = fillet(body, thickness / 12)
hl(body.forw(140))

# NECK
neck_radius = thickness / 4.0
neck_height = height / 10
neck = cylinder(r=neck_radius, h=neck_height).up(height)
body = (body + neck).solids()[0]
hl(body.forw(100))

# THICK
body = thicksolid(body, -thickness / 50, [point3(0, 0, height + height / 10)])
hl(body.forw(60))

# THREAD
cylsurf1 = cylinder_surface(neck_radius * 0.99)
cylsurf2 = cylinder_surface(neck_radius * 1.05)

major = 2 * math.pi
minor = neck_height / 10
angle = math.atan2(neck_height / 4, 2 * math.pi)

ellipse1 = ellipse2(major, minor).rotate(angle)
arc1 = cylsurf1.map(ellipse1.trim(0, math.pi))
segment1 = cylsurf1.map(segment2(ellipse1.point(0), ellipse1.point(math.pi)))

ellipse2_curve = ellipse2(major, minor / 4).rotate(angle)
arc2 = cylsurf2.map(ellipse2_curve.trim(0, math.pi))
segment2_edge = cylsurf2.map(
    segment2(ellipse2_curve.point(0), ellipse2_curve.point(math.pi))
)

m1 = sew([arc1, segment1])
m2 = sew([arc2, segment2_edge])
thread = loft([m1, m2]).up(height + neck_height / 2)

hl(m1.up(height + neck_height / 2).right(80))
hl(m2.up(height + neck_height / 2).right(60))
hl(thread.right(40))

# FINAL
m = thread + body

display(m)
show()
