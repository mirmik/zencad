from OCC.Core.TColgp import TColgp_Array1OfPnt, TColgp_HArray1OfPnt, TColgp_Array2OfPnt, TColgp_Array1OfVec
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger

from zencad.util import to_Pnt, to_Vec


def opencascade_array1_of_pnt(arr):
    ret = TColgp_Array1OfPnt(1, len(arr))
    for i in range(len(arr)):
        ret.SetValue(i + 1, to_Pnt(arr[i]))
    return ret


def opencascade_h_array1_of_pnt(arr):
    ret = TColgp_HArray1OfPnt(1, len(arr))
    for i in range(len(arr)):
        ret.SetValue(i + 1, to_Pnt(arr[i]))
    return ret


def opencascade_array1_of_vec(arr):
    ret = TColgp_Array1OfVec(1, len(arr))
    for i in range(len(arr)):
        ret.SetValue(i + 1, to_Vec(arr[i]))
    return ret


def opencascade_array2_of_pnt(arr):
    ret = TColgp_Array2OfPnt(1, len(arr), 1, len(arr[0]))
    for r in range(len(arr)):
        for c in range(len(arr[0])):
            ret.SetValue(r+1, c+1, to_Pnt(arr[r][c]))
    return ret


def opencascade_array1_of_real(arr):
    ret = TColStd_Array1OfReal(1, len(arr))
    for i in range(len(arr)):
        ret.SetValue(i + 1, float(arr[i]))
    return ret


def opencascade_array1_of_int(arr):
    ret = TColStd_Array1OfInteger(1, len(arr))
    for i in range(len(arr)):
        ret.SetValue(i + 1, int(arr[i]))
    return ret
