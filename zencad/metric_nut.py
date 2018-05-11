from zencad import *
import math

def bolt_head(h, r, n=6, angle=gr(20), f=0.3):
	r1 = r + (h-h*f) * math.cos(angle)
	r2 = r - h*f * math.cos(angle) 
	ret = linear_extrude(ngon(n=n, r=r),h) ^ cone(r1,r2,h)
	return ret

def instrument(drad, step, h):
	H = step * math.tan(gr(60))
	pseg = polysegment(points([
		(drad+H/2, 0, 0),
		(drad-H/4, 0, -(3/8*step)), 
		(drad-H/4, 0, -(5/8*step)), 
		(drad+H/2, 0, -step)
	]),closed=True)
	path = helix(radius = drad, height = h, step = step)
	base = pipe_shell(path = path, prof = pseg, frenet = True)
	return base

def metric_nut(d, step, h):
	H = step * math.tan(gr(60))
	drad = d/2 - 3/8*H
	cil = cylinder(r = d/2, h =h)
	instr = instrument(drad=drad,step=step,h=h+step)
	ret =  cil - instr
	return ret


#def bolt(e,k,L,b,d,step)
#	bolt_head(h=k, r=e/2).mirrorXY() + metric_nut(d=8, step=1.25, 30)