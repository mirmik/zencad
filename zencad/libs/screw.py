"""Бивектор углового и линейного параметра"""

import numpy
import math

import zencad.util


class screw:
    """Геометрический винт. 

    Состоит из угловой и линейной части."""

    __slots__ = ['ang', 'lin']

    def __init__(self, ang=(0, 0, 0), lin=(0, 0, 0)):
        self.ang = zencad.util.vector3(ang)
        self.lin = zencad.util.vector3(lin)

    def copy(self):
        return screw(ang=self.ang, lin=self.lin)

    def __add__(self, oth):
        return screw(self.ang + oth.ang, self.lin + oth.lin)

    def __sub__(self, oth):
        return screw(self.ang - oth.ang, self.lin - oth.lin)

    def __mul__(self, oth):
        return screw(self.ang * oth, self.lin * oth)

    def elementwise_mul(self, oth):
        # return screw((self.ang * oth.ang), self.lin * oth.lin)
        r = self.to_array() * oth.to_array()
        return screw.from_array(r)

    def __neg__(self):
        return screw(-self.ang, -self.lin)

    def scale(self, oth):
        return screw(self.ang * oth, self.lin * oth)

    def __iadd__(self, oth):
        self.ang += oth.ang
        self.lin += oth.lin
        return self

    def carry(self, arm):
        """Перенос бивектора в другую точку приложения. НА ВЕКТОР ПЛЕЧА!!! Не путать с радиус вектор.
        Вектор переноса обратен радиус вектору силы.

        Detail
        ------
        Формула TODO
        """
        return screw(
            ang=self.ang - arm.cross(self.lin),
            lin=self.lin)

    def kinematic_carry(self, arm):
        return screw(
            lin=self.lin + self.ang.cross(arm),
            ang=self.ang)

    # def inverse_kinematic_carry(self, arm):
    #	return screw(
    #		lin = self.lin - self.ang.cross(-arm),
    #		ang = self.ang )

    def angular_carry(self, arm):
        return self.kinematic_carry(arm)

    def force_carry(self, arm):
        return self.carry(arm)

    def dot(self, oth):
        l = (self.lin[0]*oth.lin[0]+self.lin[1]*oth.lin[1]+self.lin[2]*oth.lin[2] +
             self.ang[0]*oth.ang[0]+self.ang[1]*oth.ang[1]+self.ang[2]*oth.ang[2])
        # if l == 0: return 0
        return l  # math.sqrt(l)

    # def to_array(self):
        """Массив имеет обратный принятому в screw порядку"""
    #	return numpy.array([*self.lin, *self.ang])

    @staticmethod
    def from_trans(trans):
        lin = trans.translation()
        ang = trans.rotation().rotation_vector()
        return screw(lin=lin, ang=ang)

    def to_trans(self):
        trans0 = zencad.translate(*self.lin)

        rot_mul = self.ang.length()
        if rot_mul == 0:
            return trans0
        else:
            rot_dim = self.ang.normalize()
            trans1 = zencad.rotate(rot_dim, rot_mul)
            return trans0 * trans1

    def npvec_lin_first(self):
        return numpy.array([self.lin.x, self.lin.y, self.lin.z, self.ang.x, self.ang.y, self.ang.z])

    @staticmethod
    def from_array(a):
        return screw(ang=(a[3], a[4], a[5]), lin=(a[0], a[1], a[2]))

    def __str__(self):
        return "(a:({},{},{}),l:({},{},{}))".format(*self.ang, *self.lin)

    def __repr__(self):
        return "screw(a:({},{},{}),l:({},{},{}))".format(*self.ang, *self.lin)

    def inverse_rotate_by(self, trans):
        q = trans.rotation().inverse()
        return screw(ang=q.rotate(self.ang), lin=q.rotate(self.lin))

    def rotate_by(self, trans):
        return screw(ang=trans(self.ang), lin=trans(self.lin))

    def rotate_by_quat(self, q):
        return screw(ang=q.rotate(self.ang), lin=q.rotate(self.lin))


def screw_of_vector(vec, arm):
    return screw(lin=vec, ang=arm.cross(vec))


def second_kinematic_carry(iacc, ispd, arm):
    return screw(
        lin=iacc.lin + iacc.ang.cross(arm) +
        ispd.ang.cross(ispd.ang.cross(arm)),
        ang=iacc.ang
    )
