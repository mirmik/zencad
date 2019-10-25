#!/usr/bin/env python3
# coding: utf-8

from zencad import *


def section(w, h, l, t, d, d2):
    return (
        box(2 * t + w, t + l, 2 * t + h)
        - box(w, l, h).translate(t, 0, t)
        - box(w - 2 * d, l, h + 2 * t).translate(t + d, 0, 0)
        - box(w, l + t, h - d2).translate(t, 0, d2 + t)
    )


# n, m - параметры матрицы.
# w,h,l - параметры нишы.
# t - толщина стенок.
# d - выступ поддержки.
# d2 - высота заднего бампера.
def organizer(m, n, w, h, l, t, d, d2):
    sect = section(w, h, l, t, d, d2)
    line = union([sect.translate(j * (w + t), 0, 0) for j in range(0, m)])

    arr = []
    for i in range(0, n):
        arr.append(line.up(i * (h + t)))

    arr.append(box(w * m + t * (m + 1), l + t, t))
    arr.append(box(w * m + t * (m + 1), l + t, t).up(n * (h + t)))

    return union(arr)


if __name__ == "__main__":
    m = organizer(3, 5, 27, 20, 64, 1.5, 5, 5)

    display(m)
    show()
