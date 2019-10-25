from zencad import *
import zencad.assemble 
import math

def profile_height(P):
	return P * math.tan(deg(60)) / 2

def middle_diameter(D, P):
	return D - 2 * (3/8) * profile_height(P)

def internal_diameter(D, P):
	return D - 2 * (5/8) * profile_height(P)

def internal_circle_rad(R, n):
	return R * math.cos(math.pi / n)

def cropped_hexbody(R, h, angle=deg(20)):
	n = 6
	angle = deg(30)
	r = internal_circle_rad(R, n)

	m = ngon(n=n, r=R)
	m = m.extrude(h)

	outcon = cylinder(R, h) - cone(r1=R, r2=0, h=R*math.tan(angle))
	outcon1 = outcon.up(h - (R-r) * math.tan(angle))
	outcon2 = outcon.mirrorXY().up((R-r) * math.tan(angle))
	
	m = m - outcon1 - outcon2
	
	return m
	

def metric_nut_body(E, d, h, t):
	"""
		Body of metric nut.

		E - hexagon diametr
		dmin - central hole diametr
		h - height
		t - chamfer size
	"""
	m = cropped_hexbody(E/2, h)

	m = m - circle(r=d/2).extrude(h)
	m = chamfer(m, r=t, refs=[point3(0,0,0), point3(0,0,h)])

	return m

def metric_bolt_body(E, d, h, H, t):
	"""
		Body of metric nut.

		E - hexagon diametr
		dmax - bolt diameter
		h - height
		t - chamfer size
	"""
	m = cropped_hexbody(E/2, h).up(H)
	m = m + cylinder(d, H)
	m = chamfer(m, r=t, refs=[point3(0,0,0)])
	
	return m


def metric_bolt_body(d, H, t):
	"""
		Body of metric nut.

		E - hexagon diametr
		dmax - bolt diameter
		h - height
		t - chamfer size
	"""
	m = cylinder(d, H)
	m = chamfer(m, r=t, refs=[point3(0,0,0), point3(0,0,H)])
	
	return m

class metric_part(zencad.assemble.unit):
	def __init__(self, M, step):
		super().__init__()
		self.D = M
		self.d_middle =  middle_diameter(M, step)
		self.d = internal_diameter(M, step)
		self.step = step
		self.M = M


class metric_nut(metric_part):
	def __init__(self, M, E, h, step):
		super().__init__(M,step)
		self.md = metric_nut_body(E=E, d=self.d, h=h, 0)
		self.mD = metric_nut_body(E=E, d=self.D, h=h, t=self.D-self.d)
		self.add_shape(md, color=color.mech)
		self.add_shape(mD-md, color=color.transparentmech)

class metric_rod(metric_part):
	def __init__(self, M, h, step):
		super().__init__(M,step)
		self.md = metric_rod_body(self.d, 0)
		self.mD = metric_rod_body(self.D, t=self.D-self.d)
		self.add_shape(md, color=color.mech)
		self.add_shape(mD-md, color=color.transparentmech)

class metric_bolt(metric_part):
	def __init__(self, M, E, h, H, step):
		super().__init__(M,step)
		self.md = metric_bolt_body(E=E, d=self.d, h=h, H=H, t=0)
		self.mD = metric_bolt_body(E=E, d=self.D, h=h, H=H, t=self.D-self.d)
		self.add_shape(md, color=color.mech)
		self.add_shape(mD-md, color=color.transparentmech)
