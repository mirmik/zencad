#!/usr/bin/python3
#coding:utf-8

import zencad
import os

def banner(): print(zencad.shower.BANNER_TEXT)
def about(): print(zencad.shower.ABOUT_TEXT)

banner()
about()

logo = zencad.textshape("zencad", os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf"), 20)
zencad.display(logo, zencad.Color(1,1,1,0))

zencad.show()