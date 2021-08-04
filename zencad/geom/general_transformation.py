import sys
import numpy
import pickle
import base64 as b64

from OCC.Core.gp import gp_GTrsf, gp_Trsf, gp_Mat, gp_Vec, gp_Ax1, gp_Ax2, gp_Pnt, gp_Dir, gp_XYZ, gp_Quaternion

import zencad.util
#from zencad.util import point3, vector3


class GeneralTransformation:
    def __init__(self, gtrsf):
        self._gtrsf = gtrsf

    def __call__(self, obj):
        return obj.transform(self)

    def __mul__(self, oth):
        return Transformation(self._gtrsf.Multiplied(oth._gtrsf))

    def __getstate__(self):
        mat = self._gtrsf.VectorialPart()
        tra = self._gtrsf.TranslationPart()

        col1 = mat.Column(0)
        col2 = mat.Column(1)
        col3 = mat.Column(2)

        return {
            "col1": (col1.X(), col1.Y(), col1.Z()),
            "col2": (col2.X(), col2.Y(), col2.Z()),
            "col3": (col3.X(), col3.Y(), col3.Z()),
            "transl": (tra.X(), tra.Y(), tra.Z()),
        }

    def __setstate__(self, dct):
        col1 = dct["col1"]
        col2 = dct["col2"]
        col3 = dct["col3"]
        tra = dct["transl"]

        mat = gp_Mat(col1, col2, col3)

        _gtrsf = gp_GTrsf()
        _gtrsf.SetVectorialPart(mat)
        _gtrsf.SetTranslation(*tra)

    def __repr__(self):
        return b64.b64encode(pickle.dumps(self)).decode("utf-8")

    def __str__(self):
        return super().__str__()


def scaleX(a): return scaleXYZ(a, 1, 1)


def scaleY(a): return scaleXYZ(1, a, 1)


def scaleZ(a): return scaleXYZ(1, 1, a)


def scaleXYZ(x, y, z):
    gtrsf = gp_GTrsf()
    gtrsf.SetVectorialPart(gp_Mat(x, 0, 0, 0, y, 0, 0, 0, z))
    return GeneralTransformation(gtrsf)
