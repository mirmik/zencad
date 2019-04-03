#!/usr/bin/env python3
# coding: utf-8

import os
from zencad import *

fontpath = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../fonts/testfont.ttf"
)

m = textshape(text="TextShape", fontpath=fontpath, size=100)

display(m)
show()
