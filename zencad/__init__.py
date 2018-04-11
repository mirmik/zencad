import math

#widget
from zencad.widget import display
from zencad.widget import show

#cache
from zencad.cache import enable as enable_cache

#solid
from zencad.solid import box
from zencad.solid import sphere
from zencad.solid import torus
from zencad.solid import cylinder
from zencad.solid import cone

#face
from zencad.face import circle
from zencad.face import ngon
from zencad.face import square
from zencad.face import rectangle
from zencad.face import polygon

#wire
from zencad.wire import segment
from zencad.wire import polysegment
from zencad.wire import circle as wcircle
from zencad.wire import arc_by_points


def error(str):
	print("ZenCadError: " + str)
	exit(-1)

from zencad.math3 import point
from zencad.math3 import points
#from zencad.zenlib import ZenVertex as vertex

def gr(rad): return rad / 180 * math.pi
from zencad.math3 import point as pnt
