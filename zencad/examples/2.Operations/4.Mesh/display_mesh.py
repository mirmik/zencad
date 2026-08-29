from zencad import *


model = torus(30, 8) - box(60, 12, 12, center=True)
mesh = model.to_mesh(linear_deflection=0.35)

disp(mesh, color=color.orange)
show()
