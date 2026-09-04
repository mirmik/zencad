#!/usr/bin/env python3
"""Keyboard-controlled articulated chain.

Keys 1-4 select a joint; left/right rotate the selected joint.
"""

from zencad import *
import zencad.assemble


class link(zencad.assemble.unit):
    def __init__(self, h=40, axis=(0, 1, 0)):
        super().__init__()
        joint = cylinder(6, 10, center=True).transform(
            up(h) * short_rotate((0, 0, 1), axis)
        )
        self.add(cylinder(5, h) + joint)
        self.rotator = zencad.assemble.rotator(
            parent=self,
            axis=axis,
            location=up(h),
        )


a = link(axis=(0, 1, 0))
b = link(axis=(1, 0, 0))
c = link(axis=(0, 1, 0))
d = link(axis=(1, 0, 0))

a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)
d.rotator.output.add(cone(5, 12, 40).up(10) + cylinder(5, 10))

LINKS = [a, b, c, d]
COORDS = [0.0] * len(LINKS)
SELECTED = 0
SPEED = deg(90)

disp(a)


def animate(state):
    global SELECTED
    for index in range(len(LINKS)):
        if state.input.key_pressed(str(index + 1)):
            SELECTED = index

    direction = (
        state.input.key_down("right") - state.input.key_down("left")
    )
    COORDS[SELECTED] += direction * SPEED * min(state.delta, 0.1)
    for link_object, coordinate in zip(LINKS, COORDS):
        link_object.rotator.set_coord(coordinate)
    a.location_update()


show(animate=animate)
