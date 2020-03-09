#!/usr/bin/env python3
"""
ZenCad example: integration with skimage

In that example we use skimage for countors finding.
If we have contours, we can build geometry on their base.
"""


import numpy as np
#import matplotlib.pyplot as plt
import sys
from skimage import measure, io
from itertools import chain

import math
import zencad


def build():
    r = io.imread("image.png", as_gray=True)

    # Find contours at a constant value of 0.8
    contours = measure.find_contours(r, 0.8)

    zcountours = [
        zencad.interpolate([zencad.point3(t[0], t[1]) for t in contour])
        for contour in contours
    ]

    gons = [z.fill() for z in zcountours if z.is_closed()]
    ncls = [z for z in zcountours if not z.is_closed()]

    ints = []
    for i in range(0, len(gons)):
        for j in range(0, len(gons)):
            if i == j:
                continue
            ints.append(gons[i] ^ gons[j])

    ints = zencad.union(ints)
    gons = [g - ints for g in gons]

    gons = zencad.union(gons)

    pnts = chain(*[n.sfvertex().unlazy() for n in ncls])
    pnts = list(pnts)

    rpnts = []
    for i in range(0, len(pnts)):
        for j in range(0, len(pnts)):
            if i == j or j > i:
                continue
            if (
                math.sqrt(
                    (pnts[i].x - pnts[j].x) ** 2
                    + (pnts[i].y - pnts[j].y) ** 2
                    + (pnts[i].z - pnts[j].z) ** 2
                )
                < 150
            ):
                rpnts.append((i, j))

    wires = ncls + [zencad.segment(pnts[a], pnts[b]) for a, b in rpnts]

    wires = [
        wires[0],
        wires[4],
        wires[1],
        wires[7],
        wires[3],
        wires[6],
        wires[2],
        wires[5],
    ]

    gons = gons.left(760 / 2).back(768 / 2)
    w0 = zencad.sew(wires).left(760 / 2).back(768 / 2)
    w1 = w0.scale(1.2, zencad.point3(0, 0, 0))

    f = w1.fill() - w0.fill()

    mechanicus = gons + f
    mechanicus = mechanicus.extrude(20).up(20)

    base = zencad.circle(r=500).extrude(20)

    return mechanicus, base, zcountours


if __name__ == "__main__":
    mechanicus, base, zcountours = build()
    for z in zcountours:
        if z.is_closed():
            zencad.display(
                z.left(760 / 2).back(768 / 2).forw(760 + 200), zencad.color(0, 1, 0)
            )
        else:
            zencad.display(
                z.left(760 / 2).back(768 / 2).forw(760 + 200), zencad.color(1, 0, 0)
            )

    zencad.display(mechanicus, zencad.color(1, 1, 1))
    zencad.display(base, zencad.color(0.2, 0.2, 0.2))
    zencad.show()
