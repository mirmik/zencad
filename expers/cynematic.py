#!/usr/bin/env python3

import time
from zencad import *
import zencad.assemble
import zencad.cynematic
import zencad.malgo

class zv(zencad.assemble.unit):
	def __init__(self, h):
		super().__init__()
		self.m = cylinder(r=3, h=h)
		self.add_shape(self.m)

		#self.out = zencad.cynematic.spherical_rotator(parent=self, location=up(h))
		self.out = zencad.cynematic.rotator(parent=self, ax=(0,1,0), location=up(h))

o = zencad.cynematic.rotator(ax=(0,0,1))
o1 = zencad.cynematic.rotator(ax=(0,0,1), location=rotateX(deg(90)))
a = zv(60)
b = zv(60)
c = zv(60)

o.link(o1)
o1.link(a)
a.out.link(b)
b.out.link(c)

o.location_update(deep=True)



sphctr = disp(sphere(r=3))
disp(o, deep=True)
#a.bind_scene(zencad.showapi.default_scene, deep=True)

chain = zencad.cynematic.cynematic_chain(c.out)

x=[0,0,deg(-35),deg(-40),0]
#x=[0]*5
v=[0]*5

target = up(40) * left(80)
sphctr.relocate(target)

o.set_coord(x[0])
o1.set_coord(x[1])
a.out.set_coord(x[2])
b.out.set_coord(x[3])
c.out.set_coord(x[4])
o.location_update(deep=True, view=True)

start = time.time()
last = start
iteration = 0
def animate(wdg):
	global last
	global iteration
	t =  time.time() - start
	delta =t - last
	last = t


	if iteration == 0:
		iteration += 1
		return
	
	target = up(40) * left(80 - t*5)

	sens = chain.sensivity()
	linsens = [l for r,l in sens]

	current = c.out.global_location
	#diff = target
	diff = current.inverse() * target

	lintgt = diff.translation() 
	print(linsens, lintgt)

	res = zencad.malgo.grad_backpack(target = lintgt, vectors = linsens)
	res = res[0]
	print(res)
#	while(1): pass

	for i in range(len(v)):
		v[i] = res[i] * 2
		x[i] += v[i] * delta

	o.set_coord(x[0])
	o1.set_coord(x[1])
	a.out.set_coord(x[2])
	b.out.set_coord(x[3])
	c.out.set_coord(x[4])


	sphctr.relocate(target)

	o.location_update(deep=True, view=True)

#show()
show(animate=animate)
