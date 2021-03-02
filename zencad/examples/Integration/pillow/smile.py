#!/usr/bin/env python3

from zencad import *
from PIL import Image
import numpy
import evalcache


@lazy
def numpy_highmap(arr):
    result = numpy.ndarray(arr.shape, dtype=point3)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            result[i, j] = point3(i, j, arr[i, j])

    return result


img = Image.open('senku.png').convert('L')
arr = numpy.asarray(img)

pnts = numpy_highmap((1-arr/255)*8)
m = interpolate2(pnts, degmin=3, degmax=7)

disp(m)
show()
