#!/usr/bin/env python3
#coding: utf-8

from zencad import *

height = 70
width = 50
thickness = 30

pnt1 = point(-width/2.,0,0);
pnt2 = point(-width/2.,-thickness/4.,0);
pnt3 = point(0,-thickness/2.,0);
pnt4 = point(width/2,-thickness/4.,0);
pnt5 = point(width/2.,0,0);

edge1 = segment(pnt1, pnt2)
edge2 = circle_arc(pnt2, pnt3, pnt4)
edge3 = segment(pnt4, pnt5)

wire = sew([edge1, edge2, edge3])
profile = sew([wire, wire.mirrorX()])

body = profile.fill().extrude(height).fillet(thickness/12)

neck = cylinder(r=thickness/4, h=height/10).up(height)

body = body + neck

display(body)
show()