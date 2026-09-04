#!/usr/bin/env python3
"""Keyboard-controlled inverse-kinematics target.

Arrow keys move the target in X/Y; Page Up and Page Down move it in Z.
"""

from zencad import *
import zencad.assemble
import zencad.libs.kinematic
import zencad.libs.malgo


class link(zencad.assemble.unit):
    def __init__(self, h=40, axis=(0, 1, 0)):
        super().__init__()
        if axis == (0, 0, 1):
            self.add(cylinder(5, h))
        else:
            joint = cylinder(6, 10, center=True).transform(
                up(h) * short_rotate((0, 0, 1), axis)
            )
            self.add(cylinder(5, h) + joint)
        self.rotator = zencad.assemble.rotator(
            parent=self,
            axis=axis,
            location=up(h),
        )


base = zencad.assemble.rotator(axis=(0, 0, 1))
a = link(axis=(0, 1, 0))
b = link(axis=(1, 0, 0))
c = link(axis=(0, 1, 0))
d = link(axis=(1, 0, 0))
e = link(axis=(0, 1, 0))

base.link(a)
a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)
d.rotator.link(e)

LINKS = [a, b, c, d, e]
chain = zencad.libs.kinematic.kinematic_chain(LINKS[-1].rotator.output)
TARGET = [50.0, 30.0, 100.0]
TARGET_SPEED = 60.0

disp(a)
target_controller = disp(sphere(5), color.red)


def animate(state):
    delta = min(state.delta, 0.05)
    TARGET[0] += TARGET_SPEED * delta * (
        state.input.key_down("right") - state.input.key_down("left")
    )
    TARGET[1] += TARGET_SPEED * delta * (
        state.input.key_down("up") - state.input.key_down("down")
    )
    TARGET[2] += TARGET_SPEED * delta * (
        state.input.key_down("page_up") - state.input.key_down("page_down")
    )

    target_location = translate(*TARGET)
    error = (
        LINKS[-1].rotator.output.global_location.inverse()
        * target_location
    )
    coordinates, _ = zencad.libs.malgo.svd_backpack(
        error.translation(),
        vectors=[sensitivity.lin for sensitivity in chain.sensivity()],
    )

    base.set_coord(base.coord + coordinates[0] * delta)
    for index, link_object in enumerate(LINKS):
        link_object.rotator.set_coord(
            link_object.rotator.coord + coordinates[index + 1] * delta
        )

    target_controller.relocate(target_location)
    a.location_update()


show(animate=animate)
