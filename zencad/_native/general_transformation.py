import pickle
import base64 as b64

from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ


class GeneralTransformation:
    def __init__(self, gtrsf):
        self._gtrsf = gtrsf

    def __call__(self, obj):
        return obj.transform(self)

    def __mul__(self, oth):
        if not isinstance(oth, GeneralTransformation):
            return NotImplemented
        return GeneralTransformation(self._gtrsf.Multiplied(oth._gtrsf))

    def __getstate__(self):
        mat = self._gtrsf.VectorialPart()
        tra = self._gtrsf.TranslationPart()

        return {
            "matrix": tuple(
                mat.Value(row, column)
                for row in range(1, 4)
                for column in range(1, 4)
            ),
            "transl": (tra.X(), tra.Y(), tra.Z()),
        }

    def __setstate__(self, dct):
        tra = dct["transl"]
        if "matrix" in dct:
            matrix = dct["matrix"]
        else:
            # Compatibility with the historical column-oriented pickle state.
            col1 = dct["col1"]
            col2 = dct["col2"]
            col3 = dct["col3"]
            matrix = (
                col1[0], col2[0], col3[0],
                col1[1], col2[1], col3[1],
                col1[2], col2[2], col3[2],
            )
        gtrsf = gp_GTrsf()
        gtrsf.SetVectorialPart(gp_Mat(*matrix))
        gtrsf.SetTranslationPart(gp_XYZ(*tra))
        self._gtrsf = gtrsf

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
