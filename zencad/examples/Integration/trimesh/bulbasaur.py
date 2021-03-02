#!/usr/bin/env python3

import zencad

try:
    import trimesh
except:
    raise Exception(
        "You should install `trimesh` module for start this script")

h = 10
r = 30

mesh = trimesh.load('bulbasaur.STL')
bulb = zencad.polyhedron(mesh.vertices, mesh.faces)

x, y, z = bulb.center()
bulb = bulb.move(-x, -y, -z)
bbox = bulb.bbox()
bulb = bulb.up(-bbox.zrange()[0] + h)
base = zencad.cylinder(r, h)

m = base + bulb

zencad.disp(m)
zencad.show()
