#!/usr/bin/env python3
"""Orbit a model while leaving mouse interaction in control of the viewer."""

from zencad import *


model = box(10, center=True)
controller = disp(model)


def animate(state):
    # The managed runner owns model state, while the GUI owns the camera.
    # Pausing on a mouse drag keeps automatic motion out of the user's way.
    if not state.input.mouse_buttons:
        controller.relocate(rotateZ(deg(-30) * state.loctime))


show(animate=animate)
