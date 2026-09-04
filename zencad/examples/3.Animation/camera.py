#!/usr/bin/env python3
"""Orbit the viewer camera continuously, including during interaction."""

from zencad import *


model = box(10, center=True)
disp(model)


def animate(state):
    state.camera.orbit((0, 0, 1), deg(-0.8))


show(animate=animate)
