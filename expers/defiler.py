#!/usr/bin/env python3

import time
from zencad import *
import zencad.assemble
import zencad.malgo
import zencad.libs.kinematic
from zencad.libs.screw import screw

class defiler(zencad.assemble.unit):
	x = 50
	y = 20
	z = 10

	class arm(zencad.assemble.unit):
		class arm_node(zencad.assemble.unit):
			h=20
			r=1

			def __init__(self, axis=(0,1,0)):
				super().__init__()
				self.add_shape(cylinder(r=self.r, h=self.h))
				self.rot=zencad.assemble.rotator(axis=axis, location=up(self.h))
				self.link(self.rot)

		def __init__(self):
			super().__init__()
			self.arm_node_0 = self.arm_node(axis=(1,0,0))
			self.arm_node_1 = self.arm_node(axis=(1,0,0))
			#self.arm_node_2 = self.arm_node(axis=(0,1,0))
			#self.arm_node_3 = self.arm_node(axis=(1,0,0))
			#self.arm_node_4 = self.arm_node(axis=(0,1,0))
			#self.arm_node_5 = self.arm_node(axis=(0,1,0))
			#self.arm_node_6 = self.arm_node(axis=(1,0,0))

			self.link(self.arm_node_0)
			self.arm_node_0.rot.link(self.arm_node_1)
			#self.arm_node_1.rot.link(self.arm_node_2)
			#self.arm_node_2.rot.link(self.arm_node_3)
			#self.arm_node_3.rot.link(self.arm_node_4)
			#self.arm_node_4.rot.link(self.arm_node_5)
			#self.arm_node_5.rot.link(self.arm_node_6)
			self.arm_node_6 = self.arm_node_1


	
	def __init__(self):
		super().__init__()
		self.add_shape(box(self.x, self.y, self.z, center=True).fillet(3))
		
		self.arm_00 = self.arm()
		self.arm_01 = self.arm()
		self.arm_02 = self.arm()
		self.arm_03 = self.arm()
		self.arm_10 = self.arm()
		self.arm_11 = self.arm()
		self.arm_12 = self.arm()
		self.arm_13 = self.arm()



		self.brot_00 = zencad.assemble.rotator(location=move( self.x/4,self.y/2,0), axis=(0,0,1))
		self.brot_01 = zencad.assemble.rotator(location=move(        0,self.y/2,0), axis=(0,0,1))
		self.brot_02 = zencad.assemble.rotator(location=move(-self.x/4,self.y/2,0), axis=(0,0,1))
		self.brot_03 = zencad.assemble.rotator(location=move(-self.x/4*2,self.y/2,0), axis=(0,0,1))
		self.brot_10 = zencad.assemble.rotator(location=move( self.x/4,-self.y/2,0), axis=(0,0,1))
		self.brot_11 = zencad.assemble.rotator(location=move(        0,-self.y/2,0), axis=(0,0,1))
		self.brot_12 = zencad.assemble.rotator(location=move(-self.x/4,-self.y/2,0), axis=(0,0,1))
		self.brot_13 = zencad.assemble.rotator(location=move(-self.x/4*2,-self.y/2,0), axis=(0,0,1))

		self.rot_00 = zencad.assemble.rotator(axis=(1,0,0))
		self.rot_01 = zencad.assemble.rotator(axis=(1,0,0))
		self.rot_02 = zencad.assemble.rotator(axis=(1,0,0))
		self.rot_03 = zencad.assemble.rotator(axis=(1,0,0))
		self.rot_10 = zencad.assemble.rotator(axis=(-1,0,0))
		self.rot_11 = zencad.assemble.rotator(axis=(-1,0,0))
		self.rot_12 = zencad.assemble.rotator(axis=(-1,0,0))
		self.rot_13 = zencad.assemble.rotator(axis=(-1,0,0))
		
		self.arms = [self.arm_00, self.arm_01, self.arm_02, self.arm_03, self.arm_10, self.arm_11, self.arm_12, self.arm_13]
		self.rots = [self.rot_00, self.rot_01, self.rot_02, self.rot_03, self.rot_10, self.rot_11, self.rot_12, self.rot_13]
		self.brots = [self.brot_00, self.brot_01, self.brot_02, self.brot_03, self.brot_10, self.brot_11, self.brot_12, self.brot_13]

		#for rot in self.rots: rot.add_triedron()

		for i in range(len(self.arms)):
			self.link(self.brots[i])
			self.brots[i].link(self.rots[i])
			self.rots[i].link(self.arms[i])
			self.arms[i].baserot = self.brots[i]
			self.arms[i].baserot2 = self.rots[i]
			self.rots[i].set_coord(0)

		self.arm_chains = []
		for arm in self.arms:
			self.arm_chains.append(zencad.libs.kinematic.kinematic_chain(arm.arm_node_6.rot))

targets = [[],[]]

for i in range(50):
	ctr0 = disp(sphere(2),color=(0.5,0,0,0.5))
	ctr1 = disp(sphere(2),color=(0.5,0,0,0.5))
	targets[0].append(translate(i * 22,      28, -10))
	targets[1].append(translate(i * 22 +10, -28, -10))
	ctr0.relocate(targets[0][-1])
	ctr1.relocate(targets[1][-1])

targetno = [0,0,0,0,0,0,0,0]
def serve_arm(arm, arm_chain, target, delta, side, no):
	error = arm.arm_node_6.rot.global_location.inverse() * target
	sens =  arm_chain.sensivity()
	
	location_error = error.translation() * 4
	error = location_error
	sens = [(*v,) for w, v in sens]

	koeffs, iters = zencad.malgo.svd_backpack(target=error, vectors=sens)
	print(koeffs)

	arm.baserot.set_coord(arm.baserot.coord + koeffs[0] * delta)
	arm.baserot2.set_coord(arm.baserot2.coord + koeffs[1] * delta)
	if -math.pi < arm.baserot2.coord < math.pi:
		pass
	else:   arm.baserot2.coord = 0
	arm.arm_node_0.rot.set_coord(arm.arm_node_0.rot.coord + koeffs[2] * delta)
	arm.arm_node_1.rot.set_coord(arm.arm_node_1.rot.coord + koeffs[3] * delta)
	#arm.arm_node_2.rot.set_coord(arm.arm_node_2.rot.coord + koeffs[3] * delta)
	#arm.arm_node_3.rot.set_coord(arm.arm_node_3.rot.coord + koeffs[4] * delta)
	#arm.arm_node_4.rot.set_coord(arm.arm_node_4.rot.coord + koeffs[5] * delta)
	#arm.arm_node_5.rot.set_coord(arm.arm_node_5.rot.coord + koeffs[6] * delta)
	#arm.arm_node_6.rot.set_coord(arm.arm_node_6.rot.coord + koeffs[7] * delta)

	if (arm.global_location.translation() - targets[side][targetno[no]+1].translation()).length() < 30:
		targetno[no] += 1

target = [None]*8

drive=True

inited=0
starttime = time.time() 
lasttime = starttime
def animate(wdg):
	global inited
	global lasttime
	curtime = time.time()
	delta = curtime - lasttime
	lasttime = curtime
	if not inited:
		inited=True
		return

	arm = defiler.arms[0]
	arm_chain = defiler.arm_chains[0]

	target[0] = targets[0][targetno[0]]
	target[1] = targets[0][targetno[1]]
	target[2] = targets[0][targetno[2]]
	target[3] = targets[0][targetno[3]]
	target[4] = targets[1][targetno[4]]
	target[5] = targets[1][targetno[5]]
	target[6] = targets[1][targetno[6]]
	target[7] = targets[1][targetno[7]]

	serve_arm(defiler.arms[0], defiler.arm_chains[0], target[0], delta=delta, side=0,no=0)
	serve_arm(defiler.arms[1], defiler.arm_chains[1], target[1], delta=delta, side=0,no=1)
	serve_arm(defiler.arms[2], defiler.arm_chains[2], target[2], delta=delta, side=0,no=2)
	serve_arm(defiler.arms[3], defiler.arm_chains[3], target[3], delta=delta, side=0,no=3)
	serve_arm(defiler.arms[4], defiler.arm_chains[4], target[4], delta=delta, side=1,no=4)
	serve_arm(defiler.arms[5], defiler.arm_chains[5], target[5], delta=delta, side=1,no=5)
	serve_arm(defiler.arms[6], defiler.arm_chains[6], target[6], delta=delta, side=1,no=6)
	serve_arm(defiler.arms[7], defiler.arm_chains[7], target[7], delta=delta, side=1,no=7)

	if drive:
		defiler.relocate(translate(delta*15,0,0) * defiler.location)


	defiler.location_update()


defiler = defiler()

defiler.location_update()
disp(defiler)
show(animate=animate)