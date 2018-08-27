#!/usr/bin/env python3
#coding: utf-8

import zencad
import evalcache

evalcache.enable_diagnostic()

box = zencad.box(200, 200, 200, center = True)
sphere1 = zencad.sphere(120)
sphere2 = zencad.sphere(60)

union = box - sphere1 + sphere2

zencad.display(union)
zencad.show()