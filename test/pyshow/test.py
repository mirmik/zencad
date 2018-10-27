#!/usr/bin/env python3
# coding: utf-8

import sys
#import PIL
from PIL import Image
import numpy

sys.path.insert(0, '../../')

from zencad import *
import zencad.shower

m = box(100,100,100)


#scn = zencad.Scene()
#scn.add(m.unlazy())

#viewer = Viewer(scn)
#view = viewer.create_view()

#raw = view.rawarray()
#rawiter = iter(raw)
#pixels = list(reversed(list(zip(rawiter, rawiter, rawiter))))
#numpy.asarray(view.rawarray())
#image = Image.new("RGB", (800, 600))
#image.putdata(pixels)

#image.show()

#Image.fromarray(pixels, 'RGB')

#zencad.shower.show(scn)

to_stl(m, "m.stl", 0.1)

display(m)
show()