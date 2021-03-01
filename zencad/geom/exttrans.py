import numpy as np

from zencad.geom.trans import rotateZ, rotate, right, rotateX, translate
from zencad.util import deg, vector3
from zencad.geom.boolops import union

import evalcache

DEF_MTRANS_ARRAY = False
DEF_MTRANS_UNIT = False


class multitransform:
    """
            fuse: True - вернуть объединение. False - вернуть массив.
            multiply_interactive: True - делать копии интерактивных объектов и юнитов.
    """

    def __init__(self, transes, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
        self.transes = transes
        self.array = array
        self.unit = unit

    def __call__(self, shp):
        # if isinstance(shp, (
        #		pyservoce.interactive_object,
        #			zencad.assemble.unit)):
        #	rets = []
        #	clones = [shp.copy() for i in range(len(self.transes)-1)]
        #	objects = [shp] + clones

        #	lst = [ obj.transform(t) for obj, t in zip(objects, self.transes) ]

        #	if self.array:
        #		return lst
        #	else:
        #		return zencad.assemble.unit(parts=lst)

        # else:
        lst = [t(shp) for t in self.transes]
        if self.array:
            return lst

        #	if self.unit:
        #		return zencad.assemble.unit(parts=lst)

        return union(lst)


def multitrans(transes, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
    return multitransform(transes, array=array, unit=unit)


def nulltrans():
    return translate(0, 0, 0)


def sqrmirror(array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
    return multitransform([nulltrans(), mirrorYZ(), mirrorXZ(), mirrorZ()], array=array, unit=unit)


def sqrtrans(*args, **kwargs):
    print("sqrtrans renamed. use sqrmirror instead")
    return sqrmirror(*args, **kwargs)


def rotate_array(n, yaw=deg(360), endpoint=False, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
    lspace = np.linspace(0, yaw, num=n, endpoint=endpoint)
    transes = [	rotateZ(a) for a in lspace	]
    return multitrans(transes, array=array, unit=unit)


def rotate_array2(n, r=None, yaw=(0, deg(360)), roll=(0, 0), endpoint=False, array=DEF_MTRANS_ARRAY, unit=DEF_MTRANS_UNIT):
    lspace1 = np.linspace(yaw[0], yaw[1], num=n, endpoint=endpoint)
    lspace2 = np.linspace(roll[0], roll[1], num=n, endpoint=endpoint)

    transes = [
        rotateZ(a) * right(r) * rotateX(deg(90)) * rotateZ(a2) for a, a2 in zip(lspace1, lspace2)
    ]

    return multitrans(transes, array=array, unit=unit)


def short_rotate(f, t):
    f, t = vector3(evalcache.unlazy_if_need(f)), vector3(
        evalcache.unlazy_if_need(t))

    f = f / np.linalg.norm(f)
    t = t / np.linalg.norm(t)

    if np.linalg.norm(f - t) < 1e-5:
        return nulltrans()

    axis = np.cross(f, t)
    dot_product = np.dot(f, t)
    angle = np.arccos(dot_product)

    return rotate(axis, angle)
