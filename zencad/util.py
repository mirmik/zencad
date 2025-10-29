import math
import os
import numpy
import sys

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_XYZ, gp_Quaternion
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCC.Core.Geom import Geom_CartesianPoint

import zencad.geom.transformable
import evalcache

from zencad.geombase import *


def as_indexed(arg):
    if len(arg) != 1:
        return tuple(arg)
    return arg


def deg(grad):
    return float(grad) / 180.0 * math.pi


def deg2rad(d):
    return deg(d)


def rad2deg(d):
    return float(d) * 180.0 / math.pi


def angle_pair(arg):
    if isinstance(arg, tuple) or isinstance(arg, list):
        return arg

    if (arg >= 0):
        return (0, arg)
    else:
        return (arg, 0)


def examples_paths(root=None):
    import zencad
    ret = []

    if root is None:
        root = os.path.join(zencad.moduledir, "examples")
    else:
        root = os.path.abspath(root)

    for path, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if not d.startswith('__pycache__')]
        for name in files:
            if os.path.splitext(name)[1] == ".py":
                ret.append(os.path.join(path, name))

    return ret


def examples_dict(root=None):
    import zencad
    if root is None:
        root = os.path.join(zencad.moduledir, "examples")

    dct = {}
    dct["__files__"] = set()

    for d in os.listdir(root):
        dpath = os.path.join(root, d)

        if d == "__pycache__" or d == "fonts":
            continue

        if os.path.isdir(dpath):
            dct[d] = examples_dict(dpath)
        else:
            dct["__files__"].add(d)

    return dct

def _dot(a, b): return float(np.dot(a, b))

def _project_point_to_segment(p, a, b):
    # возвращает (t_clamped, closest_point)
    ab = b - a
    denom = _dot(ab, ab)
    if denom < 1e-12:
        return 0.0, a  # вырожденный отрезок
    t = _dot(p - a, ab) / denom
    t_clamped = max(0.0, min(1.0, t))
    return t_clamped, a + t_clamped * ab

def closest_points_between_segments(p0, p1, q0, q1, eps=1e-12):
    """
    Возвращает (p_near, q_near, dist) — ближайшие точки на отрезках [p0,p1] и [q0,q1] и расстояние.
    Корректно обрабатывает границы и вырожденные случаи.
    """
    u = p1 - p0
    v = q1 - q0
    w0 = p0 - q0

    a = _dot(u, u)
    b = _dot(u, v)
    c = _dot(v, v)
    d = _dot(u, w0)
    e = _dot(v, w0)
    D = a * c - b * b

    candidates = []

    # Алгоритм ищет минимум на квадрате (s,t):([0,1],[0,1])
    # 1) Внутренний кандидат
    if D > eps:
        s = (b * e - c * d) / D
        t = (a * e - b * d) / D
        if 0.0 <= s <= 1.0 and 0.0 <= t <= 1.0:
            p_int = p0 + s * u
            q_int = q0 + t * v
            candidates.append((p_int, q_int))
    # Если прямые параллельны (D<eps), то решений множество и одно из них 
    # лежит на рёбрах, поэтому ничего не делаем

    # 2) Рёбра и углы (фиксируем одну переменную и оптимизируем другую)
    # t = 0  (Q = q0) -> проектируем q0 на P
    s_t0, p_t0 = _project_point_to_segment(q0, p0, p1)
    candidates.append((p_t0, q0))

    # t = 1  (Q = q1) -> проектируем q1 на P
    s_t1, p_t1 = _project_point_to_segment(q1, p0, p1)
    candidates.append((p_t1, q1))

    # s = 0  (P = p0) -> проектируем p0 на Q
    t_s0, q_s0 = _project_point_to_segment(p0, q0, q1)
    candidates.append((p0, q_s0))

    # s = 1  (P = p1) -> проектируем p1 на Q
    t_s1, q_s1 = _project_point_to_segment(p1, q0, q1)
    candidates.append((p1, q_s1))

    # 3) Выбор лучшего кандидата
    best = None
    best_d2 = float("inf")
    for P, Q in candidates:
        d2 = _dot(P - Q, P - Q)
        if d2 < best_d2:
            best_d2 = d2
            best = (P, Q)

    p_near, q_near = best
    return p_near, q_near, float(np.sqrt(best_d2))

def closest_points_between_capsules(p0, p1, r1, q0, q1, r2):
    """
    Возвращает ближайшие точки на поверхностях двух капсул и расстояние между ними.
    Капсулы заданы своими осями (отрезками [p0,p1] и [q0,q1]) и радиусами r1, r2.
    """

    # Используем уже реализованный поиск ближайших точек между отрезками
    p_axis, q_axis, dist_axis = closest_points_between_segments(p0, p1, q0, q1)

    # Если оси почти совпадают (вектор нулевой)
    diff = p_axis - q_axis
    dist = np.linalg.norm(diff)

    # Если оси пересекаются или капсулы перекрываются
    penetration = r1 + r2 - dist

    if penetration >= 0.0:
        # Пересекаются
        p_surface = p_axis
        q_surface = q_axis
        distance = 0.0
    else:
        # Разделены
        direction = diff / dist
        p_surface = p_axis - direction * r1
        q_surface = q_axis + direction * r2
        distance = dist - (r1 + r2)

    return p_surface, q_surface, max(0.0, distance)