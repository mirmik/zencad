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

import showapi2

a = box(20,20,20) + box(10,20,30)
r=a.move(10,10,1)

r.unlazy()

#r.unwrap()
#showapi2.disp(r)
#showapi2.show(display_only=True)