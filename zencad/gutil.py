#!/usr/bin/env python3
from zencad.util import point3
from zencad.geom.trans import rotateZ
from math import sqrt


def restore_ellipse_centers(apnt, bpnt, r1, r2, phi):
    """
            Поиск центра двумерного элипса по радиусам, углу наклона главной оси и двум точкам.
    """

    rot = rotateZ(phi)
    irot = rot.inverse()

    x1, y1, _ = irot(apnt)
    x2, y2, _ = irot(bpnt)

    a, b = r1**2, r2**2

    if abs(a-b) < 1e-5 and abs(sqrt((x1-x2)**2 + (y1-y2)**2) - r1*2) < 1e-5:
        return point3((apnt.x + bpnt.x)/2, (apnt.y+bpnt.y)/2), point3((apnt.x + bpnt.x)/2, (apnt.y+bpnt.y)/2)

    if abs(x1 - x2) < 1e-5:
        y01 = (y1 + y2)/2
        x01 = x1 - sqrt(-a*b*(-4*b + y1**2 - 2*y1*y2 + y2**2))/(2*b)
        y02 = (y1 + y2)/2
        x02 = x1 + sqrt(-a*b*(-4*b + y1**2 - 2*y1*y2 + y2**2))/(2*b)

    elif abs(y1 - y2) < 1e-5:
        y01 = y1 - sqrt(-a*b*(-4*a + x1**2 - 2*x1*x2 + x2**2))/(2*a)
        x01 = (x1 + x2)/2
        y02 = y1 + sqrt(-a*b*(-4*a + x1**2 - 2*x1*x2 + x2**2))/(2*a)
        x02 = (x1 + x2)/2

    else:
        y01 = -(-a*y1**2 + a*y2**2 - b*x1**2 + b*x2**2 + (2*b*x1 - 2*b*x2)*(x1/2 + x2/2 - sqrt(-a*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2)*(-4*a *
                                                                                                                                                                     b + a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))*(y1 - y2)/(2*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))))/(2*a*(y1 - y2))
        x01 = x1/2 + x2/2 - sqrt(-a*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2)*(-4*a*b + a*y1**2 - 2*a*y1*y2 +
                                                                                                       a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))*(y1 - y2)/(2*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))

        y02 = -(-a*y1**2 + a*y2**2 - b*x1**2 + b*x2**2 + (2*b*x1 - 2*b*x2)*(x1/2 + x2/2 + sqrt(-a*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2)*(-4*a *
                                                                                                                                                                     b + a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))*(y1 - y2)/(2*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))))/(2*a*(y1 - y2))
        x02 = x1/2 + x2/2 + sqrt(-a*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2)*(-4*a*b + a*y1**2 - 2*a*y1*y2 +
                                                                                                       a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))*(y1 - y2)/(2*b*(a*y1**2 - 2*a*y1*y2 + a*y2**2 + b*x1**2 - 2*b*x1*x2 + b*x2**2))

    c0, c1 = point3(x01, y01), point3(x02, y02)
    c0, c1 = rot(c0), rot(c1)

    return c0, c1


def restore_circle_centers(apnt, bpnt, r):
    """
            Поиск центра двумерной окружности по радиусу, углу наклона главной оси и двум точкам.
    """

    return restore_ellipse_centers(apnt, bpnt, r, r, 0)


# TEST
if __name__ == "__main__":
    print(restore_ellipse_centers(point3(15, 10), point3(5, 10), 5, 5, 0))
