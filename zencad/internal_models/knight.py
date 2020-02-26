#!/usr/bin/env python3

from zencad import * 

def knight():
	base_h=  3 
	base_r1= 8
	base_r2= 6

	arrs = 	[
				[ (-2,2,0), (-2,-2,0), (2,-2,0), (2,2,0) ],
				[ (-2,2,2), (-1.5,-2.5,2), (1.5,-2.5,2), (2,2,2) ],
				[ (-3,4,5), (-2,-2,5), (2,-2, 5), (3,4,5) ],
				[ (-3,5,8), (-2,-1,8), (2,-1,8), (3,5,8) ],
				[ (-3,4,11), (-2,-1,9), (2,-1,9), (3,4,11) ],
			]

	m = union(
		[
			cylinder(r=base_r1, h=base_h),
			cone(r1=base_r1, r2=base_r2, h=base_h).up(base_h),

			loft([
				polysegment(a, closed=True) for a in arrs[:] 
			],smooth=False).up(base_h*2),
			
			#loft([
			#	polysegment(a, closed=True) for a in arrs[3:]
			#],smooth=False).up(base_h*2)
		]
	)

	return unify(m)


if __name__ == "__main__":
	disp(knight())
	show()