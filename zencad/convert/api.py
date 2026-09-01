"""Conversion boundaries for the domain API and direct GUI export."""

from __future__ import annotations

from pathlib import Path

from zencad.convert.export import export_stl
from zencad.geom.shape import Shape as ResolvedShape
from zencad.occ_compat import write_brep


def _to_stl(shape: ResolvedShape, path, delta):
    """Write a resolved viewer-side shape without constructing a domain graph."""

    if not isinstance(shape, ResolvedShape):
        raise TypeError("_to_stl expects a resolved Shape")
    export_stl(
        shape,
        str(Path(path).expanduser()),
        linear_tolerance=float(delta),
        binary=False,
    )
    return True


def _to_brep(shape: ResolvedShape, path):
    """Write a resolved viewer-side shape without constructing a domain graph."""

    if not isinstance(shape, ResolvedShape):
        raise TypeError("_to_brep expects a resolved Shape")
    if not write_brep(shape.Shape(), str(Path(path).expanduser())):
        raise OSError(f"Failed to write BREP file: {path}")


def to_stl(model, path, delta):
    from zencad._typed.conversion import to_stl as domain_to_stl

    return domain_to_stl(model, path, delta)


def to_brep(model, path):
    from zencad._typed.conversion import to_brep as domain_to_brep

    return domain_to_brep(model, path)


def from_brep(path):
    from zencad._typed.conversion import from_brep as domain_from_brep

    return domain_from_brep(path)


def to_svg(model, path, color=(0, 0, 0), mapping=False):
    from zencad._typed.conversion import to_svg as domain_to_svg

    return domain_to_svg(model, path, color, mapping)


def to_svg_string(model, color=(0, 0, 0), mapping=False):
    from zencad._typed.conversion import to_svg_string as domain_to_svg_string

    return domain_to_svg_string(model, color, mapping)


def from_svg(path):
    from zencad._typed.conversion import from_svg as domain_from_svg

    return domain_from_svg(path)


def from_svg_string(value):
    from zencad._typed.conversion import from_svg_string as domain_from_svg_string

    return domain_from_svg_string(value)


__all__ = [
    "from_brep",
    "from_svg",
    "from_svg_string",
    "to_brep",
    "to_stl",
    "to_svg",
    "to_svg_string",
]
