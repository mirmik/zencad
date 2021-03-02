import sys
import numpy
import pickle
import base64 as b64

from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax1, gp_Ax2, gp_Pnt, gp_Dir, gp_XYZ, gp_Quaternion

import zencad.util
from zencad.util import point3, vector3


class Transformation:
    def __init__(self, trsf):
        self._trsf = trsf

    def inverse(self):
        return Transformation(self._trsf.Inverted())

    def translation(self):
        xyz = self._trsf.TranslationPart()
        return zencad.util.vector3(xyz)

    def rotation(self):
        xyz = gp_XYZ()
        angle = self._trsf.GetRotation(xyz)[1]
        return zencad.util.vector3(xyz), angle

    def rotation_euler(self):
        a = self.rotation()
        return a[0] * a[1]

    def rotation_quat(self):
        q = self._trsf.GetRotation()
        return zencad.util.quat(q)

    def __call__(self, obj):
        return obj.transform(self)

    def __mul__(self, oth):
        return Transformation(self._trsf.Multiplied(oth._trsf))

    def __getstate__(self):
        scl = self._trsf.ScaleFactor()
        rot = self._trsf.GetRotation()
        tra = self._trsf.TranslationPart()

        return {
            "scale": scl,
            "rotate": (rot.X(), rot.Y(), rot.Z(), rot.W()),
            "transl": (tra.X(), tra.Y(), tra.Z()),
        }

    def __setstate__(self, dct):
        scl = dct["scale"]
        rot = dct["rotate"]
        tra = dct["transl"]

        _trsf = gp_Trsf()
        _trsf.SetRotation(*rot)
        _trsf.SetTranslation(*tra)
        _trsf.SetScale(scl)

    def __repr__(self):
        return b64.b64encode(pickle.dumps(self)).decode("utf-8")

    def __str__(self):
        return super().__str__()


def move(*args):
    xyz = zencad.util.vector3(*args)
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(xyz.x, xyz.y, xyz.z))
    return Transformation(trsf)


def translate(*args):
    return move(*args)


def right(x): return move(x, 0, 0)


def forw(y): return move(0, y, 0)


def up(z): return move(0, 0, z)


def left(x): return move(-x, 0, 0)


def back(y): return move(0, -y, 0)


def down(z): return move(0, 0, -z)


def moveX(x): return move(x, 0, 0)


def moveY(y): return move(0, y, 0)


def moveZ(z): return move(0, 0, z)


def movX(x): return move(x, 0, 0)


def movY(y): return move(0, y, 0)


def movZ(z): return move(0, 0, z)


def translateX(x): return move(x, 0, 0)


def translateY(y): return move(0, y, 0)


def translateZ(z): return move(0, 0, z)


def rotateX(a): return rotate([1, 0, 0], a)


def rotateY(a): return rotate([0, 1, 0], a)


def rotateZ(a): return rotate([0, 0, 1], a)


def rotate(axis, angle=None):
    if angle is None:
        angle = np.linalg.norm(axis)
        axis = axis / angle

    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(
        gp_Vec(axis[0], axis[1], axis[2]))), angle)
    return Transformation(trsf)


def mirror_plane(ax, ay, az):
    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(ax, ay, az)))
    return Transformation(trsf)


def mirrorXY(): return mirror_plane(0, 0, 1)


def mirrorYZ(): return mirror_plane(1, 0, 0)


def mirrorXZ(): return mirror_plane(0, 1, 0)


def mirror_axis(ax, ay, az):
    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(gp_Vec(ax, ay, az))))
    return Transformation(trsf)


def mirrorX(): return mirror_axis(1, 0, 0)


def mirrorY(): return mirror_axis(0, 1, 0)


def mirrorZ(): return mirror_axis(0, 0, 1)


def mirrorO(x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetMirror(gp_Pnt(x, y, z))
    return Transformation(trsf)


def scale(s, center=(0, 0, 0)):
    trsf = gp_Trsf()
    trsf.SetScale(point3(center).Pnt(), s)
    return Transformation(trsf)
