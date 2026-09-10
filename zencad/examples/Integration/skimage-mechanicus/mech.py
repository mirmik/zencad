#!/usr/bin/env python3
"""
ZenCad example: integration with skimage

In that example we use skimage for countors finding.
If we have contours, we can build geometry on their base.
"""
from zencad import *


import numpy as np
from skimage import measure, io
from itertools import chain, combinations
from pathlib import Path

import math


def build():
    r = io.imread(Path(__file__).with_name("image.png"), as_gray=True)

    # Find contours at a constant value of 0.8
    # Keep quarter-pixel detail without thousands of spline control points.
    contours = [
        measure.approximate_polygon(contour, tolerance=0.25)
        for contour in measure.find_contours(r, 0.8)
    ]

    zcountours = [
        polysegment(contour.tolist())
        for contour in contours
    ]

    gons = [z.fill() for z in zcountours if z.is_closed()]
    ncls = [z for z in zcountours if not z.is_closed()]

    closed = [c for c in contours if np.array_equal(c[0], c[-1])]
    bounds = [(c.min(axis=0), c.max(axis=0)) for c in closed]
    ints = []
    # Test each overlapping pair once, then subtract all holes together.
    for i, j in combinations(range(len(gons)), 2):
        lo_i, hi_i = bounds[i]
        lo_j, hi_j = bounds[j]
        if np.any(hi_i < lo_j) or np.any(hi_j < lo_i):
            continue
        ints.append(gons[i] ^ gons[j])
    gons = union(gons) - union(ints)

    pnts = chain(*(n.endpoints() for n in ncls))
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

    wires = ncls + [segment(pnts[a], pnts[b]) for a, b in rpnts]

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
    w0 = sew(wires).left(760 / 2).back(768 / 2)
    w1 = w0.scale(1.2, point3(0, 0, 0))

    f = w1.fill() - w0.fill()

    mechanicus = gons + f
    mechanicus = mechanicus.extrude(20).up(20)

    base = circle(r=500).extrude(20)

    return mechanicus, base, zcountours


if __name__ == "__main__":
    mechanicus, base, zcountours = build()
    for z in zcountours:
        if z.is_closed():
            display(
                z.left(760 / 2).back(768 / 2).forw(760 +
                                                   200), color=(0, 1, 0)
            )
        else:
            display(
                z.left(760 / 2).back(768 / 2).forw(760 +
                                                   200), color=(1, 0, 0)
            )

    display(mechanicus, color=(1, 1, 1))
    display(base, color=(0.2, 0.2, 0.2))
    show()
