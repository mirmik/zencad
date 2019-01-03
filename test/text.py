#!/usr/bin/env python3
#coding: utf-8

from zencad import *

fontpath = "/home/mirmik/project/privdocs/bujin/poster/fonts/keetano_katakana.ttf"
m = textshape("ZenCad", fontpath, 20)

#m = m.extrude(3)

display(m)
show()