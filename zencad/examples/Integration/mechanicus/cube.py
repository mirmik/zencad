#!/usr/bin/env python3

import numpy as np
#import matplotlib.pyplot as plt
import sys
from skimage import measure, io
from itertools import chain

import time
import math
import zencad

from zencad import *
import mech

mechanicus, base, ignore = mech.build()

cube = box(1000, center=True)

mech = [display(mechanicus, zencad.Color(1, 1, 1)) for i in range(0, 6)]
base = [display(base, zencad.Color(0.2, 0.2, 0.2)) for i in range(0, 6)]


def animate(wdg):
    t = time.time()
    trans = rotateZ(t) * translate(0, 0, 500)
    mech[0].relocate(trans)
    base[0].relocate(trans)
    mech[1].relocate(rotateX(deg(180)) * trans)
    base[1].relocate(rotateX(deg(180)) * trans)
    mech[2].relocate(rotateX(deg(90)) * trans)
    base[2].relocate(rotateX(deg(90)) * trans)
    mech[3].relocate(rotateX(deg(90)) * rotateX(deg(180)) * trans)
    base[3].relocate(rotateX(deg(90)) * rotateX(deg(180)) * trans)
    mech[4].relocate(rotateY(deg(90)) * trans)
    base[4].relocate(rotateY(deg(90)) * trans)
    mech[5].relocate(rotateY(deg(90)) * rotateX(deg(180)) * trans)
    base[5].relocate(rotateY(deg(90)) * rotateX(deg(180)) * trans)


display(cube, color(0.3, 0.2, 0.2))
show(animate=animate)
