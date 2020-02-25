#!/usr/bin/env python3

from zencad import * 

def knight():
	base_h=  3
	base_r1= 10
	base_r2= 7

	m = union(
		[
			cylinder(r=base_r1, h=base_h),
			cone(r1=base_r1, r2=base_r2, h=base_h).up(base_h),
			loft([
				polysegment([ (-2,2,0), (-2,-2,0), (2,-2,0), (2,2,0) ],closed=True),
				polysegment([ (-2,2,2), (-2,-2,2), (2,-2,2), (2,2,2) ],closed=True),
				polysegment([ (-3,4,4), (-2,-2,4), (2,-2,4), (3,4,4) ],closed=True),
				polysegment([ (-3,4,6), (-2,-2,6), (2,-2,6), (3,4,6) ],closed=True),
			],smooth=True).up(base_h*2)
		]
	)

	return unify(m)


if __name__ == "__main__":
	disp(knight())
	show()