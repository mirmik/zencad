#!/usr/bin/env python3
#coding: utf-8

from zencad import *
import time
import math
import termin
import termin.kinematic

tclr = color.transmech


base = assemble.unit([box(10,100,10, center=True).up(5)], name="base")
telega_act = assemble.actuator([0,1,0], name="telega_act")
azimuth_act = assemble.rotator([0,0,1], name="azimuth_act")
telega = assemble.unit([
	cylinder(5,5, center=True).up(2.5),
	box([10,40,5], center=True).up(7.5).back(15),
], name="telega")
slider_act = assemble.actuator([0,1,0], name="slider_act") 
slider = assemble.unit([
	cylinder(5,10, center=True).rotY(deg(90)).up(5)
], name="slider")
kocherga_act = assemble.rotator([1,0,0])
kocherga = assemble.unit([
	box([10,10,40], center=True).up(20)])
vslider_act = assemble.actuator([0,0,1])
vslider = assemble.unit([
    box(10,10,10, center=True).up(5)
])
elevation_act = assemble.rotator([1,0,0])
elevation = assemble.unit([
	box(10,10,5, center=True).up(2.5),
	cylinder(5, 10, center=True).rotY(deg(90))
])
antenna_link = assemble.unit([])
antenna = assemble.unit([box([10,30,5], center=True).up(2.5)])

azimuth_act.relocate(translate(0,0,0))
telega_act.relocate(translate(0,0,10))
slider_act.relocate(translate(0,0,10))
kocherga_act.relocate(translate(0,0,5))
vslider_act.relocate(translate(0,5,0))
vslider.relocate(rotateX(deg(-90)))
elevation_act.relocate(translate(0,0,10))
antenna_link.relocate(translate(0,0,5))

base.link(telega_act)
telega_act.link(azimuth_act)
azimuth_act.link(telega)
telega.link(slider_act)
slider_act.link(slider)
slider.link(kocherga_act)
kocherga_act.link(kocherga)
kocherga.link(vslider_act)
vslider_act.link(vslider)
vslider.link(elevation_act)
elevation_act.link(elevation)
elevation.link(antenna_link)
antenna_link.link(antenna)

telega_act.set_coord(30)
slider_act.set_coord(-20)
kocherga_act.set_coord(deg(45))
vslider_act.set_coord(25)
elevation_act.set_coord(deg(45))

# base.set_color(tclr)
# telega.set_color(tclr)
# slider.set_color(tclr)
# kocherga.set_color(tclr)
# vslider.set_color(tclr)

antenna.set_color(color.red)

interactive = disp(base)

prevtime = time.time()
def animate(wdg):
	delta = (time.time() - prevtime)
	azimuth_act.set_coord(deg(30) * math.sin(time.time()))
	telega_act.set_coord(30 * math.sin(time.time()))
	slider_act.set_coord(-20 + -10 * math.sin(time.time() * 1.5))
	kocherga_act.set_coord(deg(45 * math.sin(time.time() * 0.7)))
	vslider_act.set_coord(24 - 10 * math.sin(time.time() * 0.7))
	elevation_act.set_coord(deg(45 * math.sin(time.time() * 0.7)))

	interactive.location_update()

	termin.transform.inspect_tree(base.transform, name_only=True)
	raise Exception("Stop")

show(animate=animate)