#!/usr/bin/env python3

import evalcache
import zencad
import zencad.unbound.mainwindow

scn = zencad.Scene()
scn.add(evalcache.unlazy(zencad.box(10)))

zencad.unbound.mainwindow.start_application_unbound(scn)