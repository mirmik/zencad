#!/usr/bin/env python3
"""Orbit the viewer camera while mouse interaction remains in control."""

from zencad import *


model = box(10, center=True)
disp(model)


def animate(state):
    if not state.input.mouse_buttons:
        state.camera.orbit((0, 0, 1), deg(-0.8))


show(animate=animate)
