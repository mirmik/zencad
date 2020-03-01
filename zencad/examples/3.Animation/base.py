#!/usr/bin/env python3
# coding: utf-8

from zencad import *
import time

s = box(10, center=True)
controller = disp(s)

nulltime = time.time()

def animate(widget):
    trans = rotateZ(time.time() - nulltime) * right(30)
    controller.relocate(trans)

show(animate=animate)
