#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad

m = zencad.make_polysegment([])

#m = zencad.make_box(3,5,6).up(20)
#
scn = zencad.Scene()
scn.add(m)

zencad.display_scene(scn)