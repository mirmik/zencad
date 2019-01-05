#!/usr/bin/python3
#coding:utf-8

import zencad
import os

logo = zencad.textshape("zencad", os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf"), 20)
zencad.display(logo, zencad.Color(1,1,1,0))

zencad.show()