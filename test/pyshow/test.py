#!/usr/bin/python3
# coding: utf-8

import sys

sys.path.insert(0, '../../')

from zencad import *
import zencad.shower

m = box(100,100,100)

#scn = zencad.Scene()
#scn.add(m.unlazy())

#zencad.shower.show(scn)

display(m)
show()