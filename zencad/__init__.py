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


from zencad import geom as _domain
from zencad.geom import *
from zencad.cache_config import clear_cache, configure
from zencad.check import (
    CheckAssertion,
    CheckExpectations,
    CheckReport,
    CheckSubject,
    NumericRange,
    check_inspection,
    check_script,
)
from zencad.evaluation_policy import (
    EvaluationMode,
    evaluation_mode,
    set_evaluation_mode,
)
from zencad.color import (
    Color,
    black,
    blue,
    cian,
    default_border_color,
    default_color,
    default_point_color,
    default_wire_color,
    green,
    magenta,
    mech,
    orange,
    red,
    set_default_border_color,
    set_default_point_color,
    set_default_wire_color,
    transmech,
    white,
    yellow,
)
from zencad.scene import Scene
from zencad.scene_draft import SceneDraft, SceneObjectRef
from zencad.runtime.scene_protocol import SceneManifest, SceneManifestObject
from zencad.inspect import (
    InspectionObject,
    InspectionReport,
    inspect_script,
    inspect_snapshot,
)
from zencad.computation_graph import (
    ComputationGraph,
    ComputationNode,
    ComputationRoot,
    GraphArgument,
    inspect_computation_graph,
)
from zencad.render import render_script, render_snapshot
from zencad.showapi import display, disp, highlight, hl, managed_scene, show
from zencad.util import (
    closest_points_between_capsules,
    closest_points_between_segments,
    deg,
    deg2rad,
    examples_dict,
    examples_paths,
    rad2deg,
)
from zencad.version import __version__

from zencad import color as color

moduledir = os.path.dirname(__file__)
exampledir = os.path.join(os.path.dirname(__file__), "examples")

_SUPPORT_API = [
    "Color",
    "CheckAssertion",
    "CheckExpectations",
    "CheckReport",
    "CheckSubject",
    "EvaluationMode",
    "NumericRange",
    "Scene",
    "SceneDraft",
    "SceneManifest",
    "SceneManifestObject",
    "SceneObjectRef",
    "black",
    "blue",
    "cian",
    "clear_cache",
    "check_inspection",
    "check_script",
    "closest_points_between_capsules",
    "closest_points_between_segments",
    "color",
    "configure",
    "default_border_color",
    "default_color",
    "default_point_color",
    "default_wire_color",
    "deg",
    "deg2rad",
    "disp",
    "display",
    "exampledir",
    "examples_dict",
    "examples_paths",
    "evaluation_mode",
    "set_evaluation_mode",
    "green",
    "highlight",
    "hl",
    "InspectionObject",
    "InspectionReport",
    "ComputationGraph",
    "ComputationNode",
    "ComputationRoot",
    "GraphArgument",
    "inspect_computation_graph",
    "inspect_script",
    "inspect_snapshot",
    "magenta",
    "managed_scene",
    "mech",
    "moduledir",
    "orange",
    "rad2deg",
    "red",
    "render_script",
    "render_snapshot",
    "set_default_border_color",
    "set_default_point_color",
    "set_default_wire_color",
    "show",
    "transmech",
    "white",
    "yellow",
]

__all__ = [*_domain.__all__, *_SUPPORT_API]


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
