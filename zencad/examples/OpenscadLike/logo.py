#!/usr/bin/env python3
# coding: utf-8

from zencad import *


def logo(size=50):
    hole = size / 2
    cylinderHeight = size * 1.25

    cil = cylinder(r=hole / 2, h=cylinderHeight, center=True)
    m = sphere(r=size / 2) - cil - cil.rotateX(deg(90)) - cil.rotateY(deg(90))

    return m, cil


m, cil = logo(50)

hl(cil.rotateX(deg(90)))
disp(m)

show()
