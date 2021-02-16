# Based on https://github.com/qalle2/plato.scad

import math
from zencad.util import points
import zencad


def tetrahedron(r=1, a=None, shell=False):
    if a is None:
        a = r / math.sqrt(3/2) * 2

    he = a * 1 / 2        # half the edge length
    fi = a * math.sqrt(3) / 6  # faces - incircle radius
    fc = a * math.sqrt(3) / 3  # faces - circumcircle radius
    i = a * math.sqrt(6) / 12  # insphere radius
    c = a * math.sqrt(6) / 4   # circumsphere radius

    return zencad.polyhedron(
        pnts=points([
                    [0,   0,  c],  # 0: top
                    [0,  fc, -i],  # 1: bottom front
                    [-he, -fi, -i],  # 2: bottom rear left
                    [he, -fi, -i],  # 3: bottom rear right
                    ]),
        faces=[
            [1, 0, 3],  # right
            [2, 0, 1],  # left
            [3, 0, 2],  # rear
            [2, 1, 3],  # bottom
        ],
        shell=shell
    )


def hexahedron(r=1, a=None, shell=False):
    if a is None:
        a = r / math.sqrt(3) * 2

    he = a * 1 / 2        # half the edge length

    return zencad.polyhedron(
        pnts=points([
            [-he, -he, -he],  # 0
            [-he, -he,  he],  # 1
            [-he,  he, -he],  # 2
            [-he,  he,  he],  # 3
            [he, -he, -he],  # 4
            [he, -he,  he],  # 5
            [he,  he, -he],  # 6
            [he,  he,  he],  # 7
        ]),
        faces=[
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [2, 3, 7, 6],
            [0, 1, 5, 4],
            [0, 2, 6, 4],
            [1, 3, 7, 5],
        ],
        shell=shell
    )


def octahedron(r=1, a=None, shell=False):
    if a is None:
        a = r / math.sqrt(2) * 2

    he = a * 1 / 2       # half the edge length
    c = a * math.sqrt(2) / 2  # circumsphere radius

    return zencad.polyhedron(
        pnts=points([
                    [0,   0,  c],  # 0: top
                    [-he,  he,  0],  # 1: front left
                    [he,  he,  0],  # 2: front right
                    [he, -he,  0],  # 3: rear right
                    [-he, -he,  0],  # 4: rear left
                    [0,   0, -c],  # 5: bottom
                    ]),
        faces=[
            [1, 0, 2],  # top front
            [2, 0, 3],  # top right
            [3, 0, 4],  # top rear
            [4, 0, 1],  # top left
            [5, 1, 2],  # bottom front
            [5, 2, 3],  # bottom right
            [5, 3, 4],  # bottom rear
            [4, 1, 5],  # bottom left
        ],
        shell=shell
    )


def dodecahedron(r=1, a=None, shell=False):
    if a is None:
        a = r / (math.sqrt(3) * (1 + math.sqrt(5))/2) * 2

    # coordinates of the "cube"
    c = a * (1 + math.sqrt(5)) / 4  # phi / 2
    # coordinates of the "rectangular cuboid"
    r1 = a * 0
    r2 = a * (3 + math.sqrt(5)) / 4  # (phi + 1) / 2
    r3 = a * 1 / 2

    return zencad.polyhedron(
        pnts=points([
                    [r1,  r2,  r3],  # 0: front top
                    [r1,  r2, -r3],  # 1: front bottom
                    [r1, -r2,  r3],  # 2: rear top
                    [r1, -r2, -r3],  # 3: rear bottom
                    [r3,  r1,  r2],  # 4: top right
                    [r3,  r1, -r2],  # 5: bottom right
                    [-r3,  r1,  r2],  # 6: top left
                    [-r3,  r1, -r2],  # 7: bottom left
                    [c,   c,   c],  # 8: top front right
                    [c,   c,  -c],  # 9: bottom front right
                    [c,  -c,   c],  # 10: top rear right
                    [c,  -c,  -c],  # 11: bottom rear right
                    [-c,   c,   c],  # 12: top front left
                    [-c,   c,  -c],  # 13: bottom front left
                    [-c,  -c,   c],  # 14: top rear left
                    [-c,  -c,  -c],  # 15: bottom rear left
                    [r2,  r3,  r1],  # 16: right front
                    [r2, -r3,  r1],  # 17: right rear
                    [-r2,  r3,  r1],  # 18: left front
                    [-r2, -r3,  r1],  # 19: left rear
                    ]),
        faces=[
            [8, 16,  9,  1, 0],  # front right
            [12,  6,  4,  8, 0],  # top front
            [1, 13, 18, 12, 0],  # front left
            [9,  5,  7, 13, 1],  # bottom front
            [14, 19, 15,  3, 2],  # rear left
            [3, 11, 17, 10, 2],  # rear right
            [10,  4,  6, 14, 2],  # top rear
            [15,  7,  5, 11, 3],  # bottom rear
            [10, 17, 16,  8, 4],  # right top
            [9, 16, 17, 11, 5],  # right bottom
            [12, 18, 19, 14, 6],  # left top
            [15, 19, 18, 13, 7],  # left bottom
        ],
        shell=shell)


def icosahedron(r=1, a=None, shell=False):
    if a is None:
        a = r / (math.sqrt((5-math.sqrt(5))/2) * (1 + math.sqrt(5))/2) * 2

    c1 = a * 0                  # coordinate 1
    c2 = a * 1 / 2              # coordinate 2
    c3 = a * (1 + math.sqrt(5)) / 4  # coordinate 3; phi / 2

    return zencad.polyhedron(
        pnts=points([
                    [c3,  c1,  c2],  # 0: right top
                    [c3,  c1, -c2],  # 1: right bottom
                    [-c3,  c1,  c2],  # 2: left top
                    [-c3,  c1, -c2],  # 3: left bottom
                    [c2,  c3,  c1],  # 4: front right
                    [c2, -c3,  c1],  # 5: rear right
                    [-c2,  c3,  c1],  # 6: front left
                    [-c2, -c3,  c1],  # 7: rear left
                    [c1,  c2,  c3],  # 8: top front
                    [c1,  c2, -c3],  # 9: bottom front
                    [c1, -c2,  c3],  # 10: top rear
                    [c1, -c2, -c3],  # 11: bottom rear
                    ]),
        faces=[
            [1, 0,  5],  # right rear
            [4, 0,  1],  # right front
            [5, 0, 10],  # top rear right
            [8, 0,  4],  # top front right
            [10, 0,  8],  # top right
            [4, 1,  9],  # bottom front right
            [9, 1, 11],  # bottom right
            [11, 1,  5],  # bottom rear right
            [3, 2,  6],  # left front
            [6, 2,  8],  # top front left
            [7, 2,  3],  # left rear
            [8, 2, 10],  # top left
            [10, 2,  7],  # top rear left
            [7, 3, 11],  # bottom rear left
            [9, 3,  6],  # bottom front left
            [11, 3,  9],  # bottom left
            [6, 4,  9],  # front bottom
            [8, 4,  6],  # front top
            [7, 5, 10],  # rear top
            [11, 5,  7],  # rear bottom
        ],
        shell=shell)


def platonic(nfaces, r=1, a=None, shell=False):
    if nfaces == 4:
        return tetrahedron(r, a, shell)
    elif nfaces == 6:
        return hexahedron(r, a, shell)
    elif nfaces == 8:
        return octahedron(r, a, shell)
    elif nfaces == 12:
        return dodecahedron(r, a, shell)
    elif nfaces == 20:
        return icosahedron(r, a, shell)
    raise Exception("Platonic nfaces in [4,6,8,12,20]")
