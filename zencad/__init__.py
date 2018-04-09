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

def gr(rad):
	return rad / 180 * math.pi

def error(str):
	print("ZenCadError: " + str)
	exit(-1)

from zencad.math3 import point as pnt
from zencad.math3 import points
#from zencad.zenlib import ZenVertex as vertex