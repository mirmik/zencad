#!/usr/bin/env python3

import gui.display_only
import sys

from test_helper import make_test_box
from shape       import Shape
from axis        import Axis
from color       import *
from scene       import Scene
from geom2.solid import *

from interactive_object       import create_interactive_object
from trans                    import *

from util3 import *
import pickle

scene = Scene()

ddd = cylinder(r=10, h=40)# ^ box(10,10,10)
trsf = move(10,20,30) #* rotate([1,1,0], deg(20))
ddd = trsf(ddd)

scene.add(ddd, mech)

gui.display_only.init_display_only_mode()
gui.display_only.DISPLAY.attach_scene(scene)
gui.display_only.exec_display_only_mode()