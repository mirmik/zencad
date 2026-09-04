"""Compatibility alias for the geometry package formerly staged here.

The canonical domain implementation lives in :mod:`zencad.geom`.  This module
keeps existing private-preview imports working without retaining a second
implementation.
"""

from __future__ import annotations

from importlib import import_module
import sys

from zencad import geom as _geom
from zencad.geom import *  # noqa: F403


__all__ = _geom.__all__

_SUBMODULES = (
    "_boolean_operations",
    "_bound_operations",
    "_core",
    "_curve_operations",
    "_mesh_operations",
    "_operations",
    "_selector_operations",
    "_serialization",
    "_surface_operations",
    "_text_operations",
    "_transform_operations",
    "_value_operations",
    "booleans",
    "bounds",
    "context",
    "conversion",
    "curve_constructors",
    "curves",
    "exttrans",
    "face_constructors",
    "meshes",
    "modeling",
    "records",
    "selectors",
    "shape_transforms",
    "shell_constructors",
    "solid",
    "surface_topology",
    "surfaces",
    "sweeps",
    "text",
    "topology",
    "transforms",
    "values",
    "wire_builder",
)

for _name in _SUBMODULES:
    sys.modules[f"{__name__}.{_name}"] = import_module(f"zencad.geom.{_name}")

del _name
