#!/usr/bin/env python3


from zencad import *

m0 = box(10, center=True)
mesh = m0.to_mesh(0.5)
nodes = [point3(*position) for position in mesh.positions]
triangles = mesh.triangles
nsize = len(nodes)
tsize = len(triangles)

print(f"Nodes: len:{nsize} : {mesh.positions}")
print(f"Triangles: len:{tsize} : {triangles}")

m1 = polyhedron(nodes, triangles)

disp(m0)
disp(m1.right(20))

##################

m2 = cylinder(r=5, h=10, center=True)
mesh = m2.to_mesh(0.5)
nodes = [point3(*position) for position in mesh.positions]
triangles = mesh.triangles
nsize = len(nodes)
tsize = len(triangles)

print(f"Nodes: len:{nsize}")
print(f"Triangles: len:{tsize}")

m3 = polyhedron(nodes, triangles)

disp(m2.forw(20))
disp(m3.forw(20).right(20))

##################

m4 = sphere(5)
mesh = m4.to_mesh(0.5)
nodes = [point3(*position) for position in mesh.positions]
triangles = mesh.triangles
nsize = len(nodes)
tsize = len(triangles)

print(f"Nodes: len:{nsize}")
print(f"Triangles: len:{tsize}")

m5 = polyhedron(nodes, triangles)

disp(m4.forw(40))
disp(m5.forw(40).right(20))

#####################

show()
