#!/usr/bin/env python3

import zencad
import zencad.tkembed

scn = zencad.Scene()

scn.add(zencad.box(20,20,20).unlazy())

zencad.tkembed.start_window(scn)