#!/usr/bin/env python3
#coding: utf-8

from zencad import *
from zencad.nut import *

display(bolt_head(h=6, r=10).mirrorXY() + metric_nut(8, 1.25, 30))
show()