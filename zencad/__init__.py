#!/usr/bin/env python3

# Geometry API
from zencad.geom.solid import \
	box, sphere, torus, cone, cylinder, halfspace

from zencad.geom.platonic import * 

from zencad.geom.wire import \
	segment, polysegment, rounded_polysegment, interpolate, \
	circle_arc, bezier, bspline, helix

from zencad.geom.face import \
	circle, rectangle, square, polygon, ngon, textshape, \
	register_font, ellipse

from zencad.geom.shell import polyhedron

from zencad.geom.sweep import *

from zencad.geom.boolops import union, difference, intersect

from zencad.geom.exttrans import multitrans, sqrmirror, sqrtrans, \
	rotate_array, rotate_array2, short_rotate, nulltrans

from zencad.geom.unify import unify
from zencad.geom.offset import *

# Display API
from zencad.showapi import display, disp, show

# Utility
from zencad.util import *
from zencad.color import Color as color
from zencad.lazy import lazy

# Transes
from zencad.trans import move, moveX, moveY, moveZ, \
	translate, translateX, translateY, translateZ, \
	rotate, rotateX, rotateY, rotateZ, \
	mirror_axis, mirrorX, mirrorY, mirrorZ, \
	mirror_plane, mirrorXY, mirrorYZ, mirrorXZ, \
	mirrorO, \
	scale 
	# scaleX, scaleY, scaleZ

from zencad.geom.exttrans import multitrans, sqrmirror, sqrtrans, \
	rotate_array, rotate_array2, short_rotate, nulltrans

from zencad.version import __version__


moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")
