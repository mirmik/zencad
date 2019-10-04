#!/usr/bin/env python3
# coding: utf-8

from zencad import *


def case(w, h, l, t, r, z, s):
    w = w * s
    h = h * 0.95

    return (
        box(w, l, h)
        - box(w - 2 * t, l - 2 * t, h - t).translate(t, t, t)
        - cylinder(r=r, h=t + 1).rotateX(deg(90)).translate(w / 2, t + 0.5, h)
        + box(w - 2 * t, z * 2, h - r).translate(t, -z * 2, 0)
        - box(w - 2 * t - 2 * z, z, h - r - z).translate(t + z, -z, z)
        - box(w - 2 * t - 6 * z, z, h - r - 2 * z).translate(t + z * 3, -2 * z, 2 * z)
    )


if __name__ == "__main__":
    m = case(w=27, h=20, l=64, t=1.5, r=27 / 2 - 4, z=1, s=0.965)

    display(m)
    show()
