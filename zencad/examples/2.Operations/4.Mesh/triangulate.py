#!/usr/bin/env python3


from zencad import *

lazy.encache = False
lazy.decache = False
lazy.cached = False
lazy.fastdo = True

m0 = box(10, center=True)
nodes, triangles = triangulate(m0, 0.5)

nodes_unlazy = nodes.unlazy()
nsize = len(nodes_unlazy)

triangles_unlazy = triangles.unlazy()
tsize = len(triangles_unlazy)

print(f"Nodes: len:{nsize} : {nodes_unlazy}")
print(f"Triangles: len:{tsize} : {triangles_unlazy}")

m1 = polyhedron(nodes, triangles)

disp(m0)
disp(m1.right(20))

##################

m2 = cylinder(r=5, h=10, center=True)
nodes, triangles = triangulate(m2, 0.5)

nodes_unlazy = nodes.unlazy()
nsize = len(nodes_unlazy)

triangles_unlazy = triangles.unlazy()
tsize = len(triangles_unlazy)

print(f"Nodes: len:{nsize}")
print(f"Triangles: len:{tsize}")

m3 = polyhedron(nodes, triangles)

disp(m2.forw(20))
disp(m3.forw(20).right(20))

##################

m4 = sphere(5)
nodes, triangles = triangulate(m4, 0.5)

nodes_unlazy = nodes.unlazy()
nsize = len(nodes_unlazy)

triangles_unlazy = triangles.unlazy()
tsize = len(triangles_unlazy)

print(f"Nodes: len:{nsize}")
print(f"Triangles: len:{tsize}")

m5 = polyhedron(nodes, triangles)

disp(m4.forw(40))
disp(m5.forw(40).right(20))

#####################

show()
