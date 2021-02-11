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

a = box(20,20,20)
a.unlazy()

b= box(10,10,10)
b.unlazy()

m = (a + b).move(5,5,10)
m.unlazy()
#showapi2.disp(m)
#showapi2.show(display_only=True)