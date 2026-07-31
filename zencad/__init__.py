#!/usr/bin/env python3

import importlib
import os

try:
    import OCP
    import OCP.gp
except ImportError as exception:
    raise ImportError(
        "ZenCad requires cadquery-ocp-novtk; install it with "
        "'python -m pip install zencad'"
    ) from exception

from zencad.version import __ocp_version__


try:
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
    from zencad.showapi import display, disp, show, hl, highlight, managed_scene
    from zencad.scene import Scene
    from zencad.scene_draft import SceneDraft, SceneObjectRef

    # Utility
    from zencad.util import *
    from zencad.color import Color
    from zencad.color import default_color, set_default_point_color, default_point_color
    from zencad.color import set_default_wire_color, default_wire_color
    from zencad.color import set_default_border_color, default_border_color
    import zencad.color as color
    from zencad.lazifier import lazy

    from zencad.color import (white,
black,
red,
green,
blue,
yellow,
magenta,
cian,
mech,
transmech,
orange)

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

except ImportError:
    raise

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")


def __getattr__(name):
    """Load the local assembly API only when it is requested."""
    if name != "assemble":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        module = importlib.import_module("zencad.assemble")
    except ImportError as exception:
        raise ImportError(
            "zencad.assemble could not load its local kinematic API"
        ) from exception

    globals()[name] = module
    return module
