#!/usr/bin/env python3

from zencad.version import __occt_version__, __pythonocc_version__
import os
import sys
from zencad.version import __occt_version__

# Libraries loading test. Starts with gui mode only.

if (
    (True
     #        sys.platform == "win32" or
     #       sys.argv[0][-7:] == "/zencad"
     #      or
     #     sys.argv[0] == "zencad"
     #    or
     #   (len(sys.argv) > 2 and sys.argv[1]
     #   == "-m" and sys.argv[2] == "zencad")
     # or
        # (len(sys.argv) >= 2 and sys.argv[0]
     # == "-m" and sys.argv[1] == "zencad")
     )
    and not "--display-only" in sys.argv
    and not "--install-pythonocc" in " ".join(sys.argv)
    and not "--install-occt" in " ".join(sys.argv)
):
    try:
        import OCC
        import OCC.Core.gp
    except:
        import zencad.gui.libinstaller
        zencad.gui.libinstaller.doit()
        exit()


class PreventLibraryLoading(Exception):
    pass


try:
    # Если активирована опция переустановки библиотек,
    # не даём интерпретатору линковать имеющиеся
    if ("--install-occt" in " ".join(sys.argv) or
            "--install-pythonocc" in " ".join(sys.argv)):
        print("Prevent library link.")
        raise PreventLibraryLoading()

    # Geometry API
    from zencad.geom.solid import *
    from zencad.geom.platonic import *
    from zencad.geom.wire import *
    from zencad.geom.face import *
    from zencad.geom.shell import *
    from zencad.geom.sweep import *
    from zencad.geom.boolops import *
    from zencad.geom.exttrans import *
    from zencad.geom.unify import *
    from zencad.geom.offset import *
    from zencad.geom.operations import *
    from zencad.geom.wire_builder import wire_builder
    from zencad.geom.near import *

    # Display API
    from zencad.showapi import display, disp, show, hl, highlight
    from zencad.scene import Scene

    # Utility
    from zencad.util import *
    from zencad.color import Color
    from zencad.color import default_color
    import zencad.color as color
    from zencad.lazifier import lazy

    import zencad.assemble

    # Transes
    from zencad.geom.trans import move, moveX, moveY, moveZ, \
        translate, translateX, translateY, translateZ, \
        rotate, rotateX, rotateY, rotateZ, \
        mirror_axis, mirrorX, mirrorY, mirrorZ, \
        mirror_plane, mirrorXY, mirrorYZ, mirrorXZ, \
        mirrorO, \
        scale, \
        up, down, left, right, forw, back

    from zencad.geom.general_transformation import scaleXYZ, scaleX, scaleY, scaleZ

    from zencad.geom.exttrans import multitrans, sqrmirror, sqrtrans, \
        rotate_array, rotate_array2, short_rotate, nulltrans

    from zencad.version import __version__

    from zencad.convert.api import *

except ImportError as ex:
    if "libTK" in str(ex):
        print("OCCT is not installed")
    else:
        raise ex
except PreventLibraryLoading as ex:
    pass

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")
