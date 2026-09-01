#!/usr/bin/env python3
# coding: utf-8

from zencad import *

thikness = 2.5
height = 90
radius = 40
handle_radius = 5

pnts = [point3(x, 0, z) for x, z in [(-5, -5), (0, 0), (27, 40), (25, 50), (5, 60), (-5, 60)]]

tangs = [vector3(x, 0, z) for x, z in [(1, 1), (1, 1), (0, 0), (0, 0), (0, 0), (0, 0)]]

# Base:
base = cylinder(r=radius, h=height)
hole = cylinder(r=radius - thikness, h=height - thikness).up(thikness)

# Handle:
spine = interpolate(pnts, tangs).rotateX(deg(90))
profile = circle(handle_radius).rotateY(
    deg(45)).translate(pnts[0].x.value(), 0, pnts[0].z.value())
handle = pipe(profile, spine)

# Assemble:
cup = base + handle.right(40).up(17) - hole

# Display:
hl(spine.right(100).up(17).forw(20))
hl(profile.right(100).up(17).forw(20))
hl(handle.right(100).up(17).back(20))
display(cup)

show()
