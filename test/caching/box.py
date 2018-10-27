#!/usr/bin/env python3
#coding: utf-8

import zencad
import zencad.future_cache

import evalcache

evalcache.enable()

m = zencad.future_cache.box(20, 80, 10)
zencad.display(m.eval())

zencad.show()