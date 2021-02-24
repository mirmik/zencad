#!/usr/bin/env python3

import os
import sys

# Libraries loading test. Starts with gui mode only.
if (
    (
        sys.argv[0][-7:] == "/zencad"
        or
        sys.argv[0] == "zencad"
        or
        (len(sys.argv) > 2 and sys.argv[1]
         == "-m" and sys.argv[2] == "zencad")
    )
    and
    not "--display-only" in sys.argv
):
    try:
        import OCC
        import OCC.Core.gp
    except:
        import zencad.gui.libinstaller
        zencad.gui.libinstaller.doit()
        exit()


from zencad.version import __occt_version__, __pythonocc_version__


class PreventLibraryLoading(Exception):
    pass


try:
    # Если активировано опция переустановки библиотек,
    # не даём интерпретатору линковать имеющиеся
    if ("--install-occt" in " ".join(sys.argv) or
            "--install-pythonocc" in " ".join(sys.argv)):
        print("Prevent library link.")
        raise PreventLibraryLoading()

    # Geometry API
    from zencad.geom.solid import \
        box, sphere, torus, cone, cylinder, halfspace

    from zencad.geom.platonic import *

    from zencad.geom.wire import \
        segment, polysegment, rounded_polysegment, interpolate, \
        circle_arc, bezier, bspline, helix

    from zencad.geom.face import \
        circle, rectangle, square, polygon, ngon, textshape, \
        register_font, ellipse

    from zencad.geom.shell import polyhedron

    from zencad.geom.sweep import *

    from zencad.geom.boolops import union, difference, intersect

    from zencad.geom.exttrans import multitrans, sqrmirror, sqrtrans, \
        rotate_array, rotate_array2, short_rotate, nulltrans

    from zencad.geom.unify import unify
    from zencad.geom.offset import *

    # Display API
    from zencad.showapi import display, disp, show
    from zencad.scene import Scene

    # Utility
    from zencad.util import *
    from zencad.color import Color as color
    from zencad.lazifier import lazy

    # Transes
    from zencad.geom.trans import move, moveX, moveY, moveZ, \
        translate, translateX, translateY, translateZ, \
        rotate, rotateX, rotateY, rotateZ, \
        mirror_axis, mirrorX, mirrorY, mirrorZ, \
        mirror_plane, mirrorXY, mirrorYZ, mirrorXZ, \
        mirrorO, \
        scale, \
        up, down, left, right, forw, back
    # scaleX, scaleY, scaleZ

    from zencad.geom.exttrans import multitrans, sqrmirror, sqrtrans, \
        rotate_array, rotate_array2, short_rotate, nulltrans

    from zencad.version import __version__

except ImportError as ex:
    if "libTK" in str(ex):
        print("OCCT is not installed")
    else:
        raise ex
except PreventLibraryLoading as ex:
    pass

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")
