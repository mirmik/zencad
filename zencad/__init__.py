import math
#import lazy_import

import pyservoce
from pyservoce import point3, vector3
from pyservoce import Scene, View, Viewer, Color
from pyservoce import Color as color
from pyservoce import point3 as point
from pyservoce import vector3 as vector

#zencad_visual = lazy_import.lazy_module("zencad.visual")
from zencad.visual import screen
from zencad.transform import *

from zencad.lazifier import lazy, shape_generator, nocached_shape_generator
from zencad.lazifier import disable_cache, test_mode
import evalcache

from zencad.util import deg, angle_pair, points, vectors
from zencad.convert import *
import types

#__version__ = 
moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")

from zencad.showapi import show, display, disp, hl, highlight 

from zencad.prim3d import *
from zencad.prim2d import *
from zencad.prim1d import *

from zencad.ops3d import *
from zencad.ops1d2d import *





#@lazy.lazy(cls=nocached_shape_generator)
#def wcircle(*args, **kwargs):
#	print("def wcircle(*args, **kwargs): deprecated")
#	return pyservoce.make_wcircle(*args, *kwargs)

#@lazy.lazy(cls=shape_generator)
#def sweep(prof, path):
#	print("def sweep(prof, path): deprecated")
#	return pyservoce.make_sweep(prof, path)

def gr(grad): 
	print("'gr' function is deprecated. Use 'deg' instead")
	return float(grad) / 180.0 * math.pi

def enable_cache_diagnostic():
	evalcache.diagnostic = True

#def screen(*args, **kwargs):
#	return zencad_visual.screen(*args, **kwargs)


@lazy.lazy(cls=shape_generator)
def near_edge(*args, **kwargs): return pyservoce.near_edge(*args, **kwargs)

@lazy.lazy(cls=shape_generator)
def near_face(*args, **kwargs): return pyservoce.near_face(*args, **kwargs)

@lazy.lazy(cls=shape_generator)
def near_vertex(*args, **kwargs): return pyservoce.near_vertex(*args, **kwargs)


