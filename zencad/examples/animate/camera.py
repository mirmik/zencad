#!/usr/bin/env python3
# coding: utf-8

from zencad import *
import time

s = box(10, center=True)
controller = disp(s)


def animate(wdg):
    if not wdg.mousedown:
        wdg.set_eye(zencad.rotateZ(zencad.deg(-0.8))(wdg.eye()), orthogonal=True)


show(animate=animate)
