#!/usr/bin/env python3

import gui.display_only
import sys

from shape       import Shape
from axis        import Axis
from color       import *
from scene       import Scene
from geom2.solid import *
from geom2.face import *
from geom2.wire import *

from interactive_object       import create_interactive_object
from trans                    import *

from util3 import *
import pickle

import showapi2

a = circle(10, yaw=(0,deg(145)))
showapi2.disp(a)
showapi2.show(display_only=True)