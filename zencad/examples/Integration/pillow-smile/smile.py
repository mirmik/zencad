#!/usr/bin/env python3

from zencad import *
from PIL import Image
import numpy
import evalcache

img = Image.open('smile.png').convert('L')
arr = numpy.asarray(img)

pnts = numpy_highmap(1-arr/255)
m = interpolate2(pnts, degmin=2, degmax=7)

disp(m)
show()