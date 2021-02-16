#!/usr/bin/env python3

from zencad import *


def knight():
    base_h = 3
    base_r1 = 8
    base_r2 = 6

    body_pnts = [
        points([(-2, 2, 0), (-2, -2, 0), (2, -2, 0), (2, 2, 0)]),
        points([(-2, 2, 2), (-1.5, -2.5, 2), (1.5, -2.5, 2), (2, 2, 2)]),
        points([(-3, 4, 5), (-2, -2, 5), (2, -2, 5), (3, 4, 5)]),
        points([(-3, 5, 8), (-2, -1, 8), (2, -1, 8), (3, 5, 8)]),
        points([(-3, 4, 11), (-2, -1, 9), (2, -1, 9), (3, 4, 11)]),
    ]

    head1_pnts = [
        points([body_pnts[-1][0], body_pnts[-1][-1],
                body_pnts[-1][-1] + vector3(0.5, 1, 1), body_pnts[-1][0] + vector3(-0.5, 1, 1), ]),
        points([(-2, -1, 9), (2, -1, 9), (3, -1, 12), (-3, -1, 12), ]),
        points([(-0.5, -6, 8), (0.5, -6, 8), (1, -7, 9), (-1, -7, 9), ]),
    ]

    head2_pnts = [
        [head1_pnts[0][-2], head1_pnts[0][-1],
         head1_pnts[0][-1] + vector3(0, 0.5, 1.5), head1_pnts[0][-2] + vector3(0, 0.5, 1.5)],
        [head1_pnts[1][-2], head1_pnts[1][-1],
         head1_pnts[1][-1] + vector3(0, 0, 1), head1_pnts[1][-2] + vector3(0, 0, 1)],
        [head1_pnts[2][-2], head1_pnts[2][-1],
         head1_pnts[2][-1] + vector3(0, 0, 1), head1_pnts[2][-2] + vector3(0, 0, 1)],
    ]

    head3_pnts = [
        [head2_pnts[0][-2], head2_pnts[0][-1],
         head2_pnts[0][-1] + vector3(-1.5, -1, 2), head2_pnts[0][-2] + vector3(1.5, -1, 2)],
        [head2_pnts[1][-2], head2_pnts[1][-1],
         head2_pnts[1][-1] + vector3(-1.5, 0, 2), head2_pnts[1][-2] + vector3(1.5, 0, 2)],
        [head2_pnts[2][-2], head2_pnts[2][-1],
         head2_pnts[2][-1] + vector3(-0.3, 0.8, 0.8), head2_pnts[2][-2] + vector3(0.3, 0.8, 0.8)],
    ]

    m = union(
        [
            cylinder(r=base_r1, h=base_h),
            cone(r1=base_r1, r2=base_r2, h=base_h).up(base_h),

            loft([
                polysegment(a, closed=True) for a in body_pnts
            ], smooth=False).up(base_h*2),

            loft([
                polysegment(a, closed=True) for a in head1_pnts
            ], smooth=False).up(base_h*2),

            loft([
                polysegment(a, closed=True) for a in head2_pnts
            ], smooth=False).up(base_h*2),

            loft([
                polysegment(a, closed=True) for a in head3_pnts
            ], smooth=False).up(base_h*2),
        ]
    )

    return unify(m).fillet(0.14)


if __name__ == "__main__":
    knight()
    disp(knight())
    show()
