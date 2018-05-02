#!/usr/bin/env python3
#coding: utf-8

from zencad import *
#import zencad.nut

#m = zencad.nut.base_nut()

#OpenCascade дает ошибки при совпадении сложных поверхностей, поэтому внутри данной библиотеки 
#внутренние размеры часто увеличены на 10%. Это позволяет алгоритму работать в комфортных условиях.

#def base_nut(irad, orad, h, step, invert = False):
#	off = step * 0.1 / 2
#	mstep = step * 1.1
#	ch_irad = irad / 1.1
#	ch_orad = orad * 1.1
#	if invert:
#		pseg = polysegment(points([(ch_irad, 0, -off), (orad, 0, mstep/2-off), (ch_irad, 0, mstep-off)]),closed=True)
#		path = helix(radius = irad, height = h, step = step).up(step-off)
#		base = pipe_shell(path = path, prof = pseg, frenet = True)
#		#display(pseg)
#		#display(path)
##		display(base)
#		return base
#	else:
#		pseg = polysegment(points([(irad, 0, step/2), (ch_orad, 0, mstep), (ch_orad, 0, 0)]),closed=True)
#		path = helix(radius = orad, height = h, step = step)
#		base = pipe_shell(path = path, prof = pseg, frenet = True)
#		return base

def instrument_metric_nut(drad, step, h):
	#pseg = polysegment(points([(irad, 0, -step/2), (orad*2, 0, -step), (orad*2, 0, 0)]),closed=True)
	H = step * math.tan(gr(60))

	pseg = polysegment(points([
		(drad+H/2, 0, 0),
		(drad-H/4, 0, -(3/8*step)), 
		(drad-H/4, 0, -(5/8*step)), 
		(drad+H/2, 0, -step)
	]),closed=True)
	
	#return pseg

	path = helix(radius = drad, height = h, step = step)
	base = pipe_shell(path = path, prof = pseg, frenet = True)
	return base

def metric_nut(d, step, h):
	H = step * math.tan(gr(60))
	drad = d/2 - 3/8*H
	cil = cylinder(r = d/2, h =h)
	instr = instrument_metric_nut(drad=drad,step=step,h=h+step)
	ret =  cil - instr
	#ret = union([
	#	ret.up(step*i) for i in range(0,20)
	# ])

	#display(instr)
	#display(cil)
	#display(ret)

	return ret

m = metric_nut(8, 1.25, 30).up(25.3) + cylinder(r=8/2, h=20).up(5.3) + linear_extrude(ngon(r = 7.1, n=6),(0,0,5.3))


#box(20,20,20).translate(-10,-10,0) - metric_nut(8, 1.25, 20)
display(m)

#make_stl("nt.stl", metric_nut(6, 1, 8))

#
#def base_nut_profile(irad, orad, step):
#	return circle(orad+10) - __base_nut(irad, orad, step)	
#
#def nut(irad, orad, step, h):
#	path = helix(radius = irad, height = h, step = step) #^ cylinder(r = orad, h = h)
#	base = base_nut_profile(irad, orad, step)
#	
#	wr1 = base.wires()[0]
#	#wr2 = simplify_with_bspline(base.wires()[1])
#	#display(wr1)
#	#edg = base.wires()[0].parts()[0]
#
#	#base.wires()[0] - box(orad*2.5,center=True).back(orad*2.5/2)
#	#b_base =   #base.wires()[0] - box(orad*2.5,center=True).forw(orad*2.5/2)
#
#	#display(a_base)
#	#display().face())
#
#
#	#base = rectangle(a = 20, b= 40, center= True)
#
#	#display(path)
#	#display(path)
#	#display(base.wires()[0])
#	#return pipe(path = path, prof = base)
#	return pipe_shell(path = path, prof = wr1, frenet = True)
##	#return pipe_shell(path = path, prof = base, frenet = True)
#
#
#n = 10
#
#nt = nut(irad = 18, orad = 20, step = 2, h = 0.5)
#
#m = union([nt.rotateZ(gr(90)*i).up(0.5*i) for i in range(0,12)])
#
##union([nut(irad = 18, orad = 20, step = 2, h =2).up(i*2) for i in range(0,n)])
#
##make_stl("nut.stl", m)
##m = nut(irad = 18, orad = 20, step = 2, h =10)
##c = cylinder(r=10, h = 10 + 10).down(5).right(8)
##c = box(50,50,2, center=True)
##
##make_stl("box.stl", c)
#
#
##make_stl("mc.stl", c - m)
##display(c-m)
#display(m)
##display(m.right(30))

#m = cylinder(r = 30, h = 10) - m

#def nut(irad, orad, h, step):
#	base = base_nut(irad, orad, h + step, step, True)
#	return base + cylinder(r=irad,h=h+3*step).down(step/2)

#display(base_nut(10,20,50,10,True)
#m = circle(20) - base_nut(10,20,10)
#display(base_nut(10,20,50,10,True))
#display(base_nut(10,20,50,10,True) + cylinder(r = 10, h = 60))
#display(c)
#display(m)
show()