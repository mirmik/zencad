#! /usr/bin/env python3
import numpy as np

import numpy as np

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

    # 1) Внутренний кандидат (на бесконечных прямых)
    if D > eps:
        s = (b * e - c * d) / D
        t = (a * e - b * d) / D
        if 0.0 <= s <= 1.0 and 0.0 <= t <= 1.0:
            p_int = p0 + s * u
            q_int = q0 + t * v
            candidates.append((p_int, q_int))

    # 2) Рёбра (фиксируем одну переменную и оптимизируем другую)
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

import numpy as np

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


# ==== пример ==== 

import numpy as np
EPS = 1e-8

def assert_close(a, b, eps=EPS):
    if not np.allclose(a, b, atol=eps):
        raise AssertionError(f"{a} != {b}")

def assert_scalar_close(a, b, eps=EPS):
    if abs(a - b) > eps:
        raise AssertionError(f"{a} != {b}")


def test_intersecting_segments():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    q0 = np.array([0.5, -1.0, 0.0])
    q1 = np.array([0.5,  1.0, 0.0])

    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_close(p, [0.5, 0.0, 0.0])
    assert_close(q, [0.5, 0.0, 0.0])
    assert_scalar_close(d, 0.0)


def test_parallel_offset_segments():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    q0 = np.array([0.0, 1.0, 0.0])
    q1 = np.array([1.0, 1.0, 0.0])

    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_scalar_close(d, 1.0)
    assert_close(p - q, [0.0, -1.0, 0.0])


def test_skew_segments_3d():
    p0 = np.array([0, 0, 0])
    p1 = np.array([1, 0, 0])
    q0 = np.array([0, 1, 1])
    q1 = np.array([2, 1, -1])

    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_scalar_close(d, 1.0)


def test_touching_at_endpoint():
    p0 = np.array([0, 0, 0])
    p1 = np.array([1, 0, 0])
    q0 = np.array([1, 0, 0])
    q1 = np.array([2, 1, 0])

    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_scalar_close(d, 0.0)
    assert_close(p, q)


def test_minimum_on_endpoint():
    p0 = np.array([0, 0, 0])
    p1 = np.array([1, 0, 0])
    q0 = np.array([2, 1, 0])
    q1 = np.array([2, -1, 0])

    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_close(p, [1.0, 0.0, 0.0])
    assert_scalar_close(d, 1.0)


def test_degenerate_segments():
    p0 = p1 = np.array([1.0, 2.0, 3.0])
    q0 = q1 = np.array([1.0, 3.0, 3.0])
    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_close(p, p0)
    assert_close(q, q0)
    assert_scalar_close(d, 1.0)


def test_one_degenerate_segment():
    p0 = p1 = np.array([0.0, 0.0, 0.0])
    q0 = np.array([1.0, 0.0, 0.0])
    q1 = np.array([1.0, 1.0, 0.0])
    p, q, d = closest_points_between_segments(p0, p1, q0, q1)
    assert_scalar_close(d, 1.0)
    assert_close(p, [0.0, 0.0, 0.0])
    assert_close(q, [1.0, 0.0, 0.0])

def assert_close(a, b, eps=EPS):
    if not np.allclose(a, b, atol=eps):
        raise AssertionError(f"{a} != {b}")


def assert_scalar_close(a, b, eps=EPS):
    if abs(a - b) > eps:
        raise AssertionError(f"{a} != {b}")


def test_non_intersecting_capsules():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    r1 = 0.5

    q0 = np.array([0.5, 2.0, 0.0])
    q1 = np.array([0.5, 3.0, 0.0])
    r2 = 0.25

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert d > 0
    assert_scalar_close(d, 2.0 - (r1 + r2))  # расстояние между поверхностями
    assert abs(np.linalg.norm(p - q) - (d)) < EPS


def test_touching_capsules():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    r1 = 0.5

    q0 = np.array([0.5, 1.25, 0.0])
    q1 = np.array([0.5, 2.25, 0.0])
    r2 = 0.25

    # сдвигаем чуть ближе, чтобы касались
    q0[1] = 0.75
    q1[1] = 1.75

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert_scalar_close(d, 0.0)
    assert np.linalg.norm(p - q) <= r1 + r2 + EPS


def test_intersecting_capsules():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    r1 = 0.5

    q0 = np.array([0.5, 0.3, 0.0])
    q1 = np.array([0.5, 1.3, 0.0])
    r2 = 0.4

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert_scalar_close(d, 0.0)  # пересечение
    assert np.linalg.norm(p - q) < r1 + r2 + EPS


def test_parallel_capsules_far_apart():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([2.0, 0.0, 0.0])
    r1 = 0.2

    q0 = np.array([0.0, 2.0, 0.0])
    q1 = np.array([2.0, 2.0, 0.0])
    r2 = 0.3

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert_scalar_close(d, 2.0 - (r1 + r2))
    assert abs(np.linalg.norm(p - q) - (d)) < EPS


def test_overlapping_axes_capsules():
    # Совпадающие оси, но разные радиусы
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    r1 = 0.5

    q0 = np.array([0.2, 0.0, 0.0])
    q1 = np.array([0.8, 0.0, 0.0])
    r2 = 0.3

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert_scalar_close(d, 0.0)
    assert np.linalg.norm(p - q) <= r1 + r2 + EPS


def test_degenerate_capsules_points():
    # Капсулы вырожденные в сферы
    p0 = p1 = np.array([0.0, 0.0, 0.0])
    q0 = q1 = np.array([2.0, 0.0, 0.0])
    r1, r2 = 0.5, 0.25

    p, q, d = closest_points_between_capsules(p0, p1, r1, q0, q1, r2)
    assert_scalar_close(d, 2.0 - (r1 + r2))
    assert_close(p, [0.5, 0.0, 0.0])
    assert_close(q, [1.75, 0.0, 0.0])

def run_all_tests():
    tests = [
        test_intersecting_segments,
        test_parallel_offset_segments,
        test_skew_segments_3d,
        test_touching_at_endpoint,
        test_minimum_on_endpoint,
        test_degenerate_segments,
        test_one_degenerate_segment,

        test_non_intersecting_capsules,
        test_touching_capsules,
        test_intersecting_capsules,
        test_parallel_capsules_far_apart,
        test_overlapping_axes_capsules,
        test_degenerate_capsules_points,
    ]

    print("🚀 Запуск тестов для closest_points_between_segments...\n")
    for i, test in enumerate(tests, 1):
        try:
            test()
            print(f"✅ Тест {i}: {test.__name__} — OK")
        except Exception as e:
            print(f"❌ Тест {i}: {test.__name__} — FAIL\n   {e}")
            

    print("\n🎉 Все тесты прошли успешно!")


if __name__ == "__main__":
    run_all_tests()