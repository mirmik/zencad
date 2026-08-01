#!/usr/bin/env python3
# coding: utf-8
"""Legacy direct-GUI example; managed camera commands are not available yet."""

from zencad import *
import time

s = box(10, center=True)
controller = disp(s)


def animate(wdg):
    if not wdg.mousedown:
        wdg.set_eye(zencad.rotateZ(zencad.deg(-0.8))(wdg.eye()), orthogonal=True)


show(animate=animate)
