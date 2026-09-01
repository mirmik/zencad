"""Immediate typed file and text conversion boundaries."""

from __future__ import annotations

from collections.abc import Mapping
import math
from os import PathLike
from pathlib import Path
from typing import BinaryIO

import evalcache
from OCP.TopoDS import TopoDS_Shape

from zencad.convert.export import (
    LengthUnit,
    export_3mf as _export_3mf,
    export_step as _export_step,
    export_stl as _export_stl,
)
from zencad.convert.svg import SvgReader, shape_to_svg_string
from zencad.geom.shape import Shape as ResolvedShape
from zencad.occ_compat import read_brep, write_brep
from zencad.operation import resolve_context

from .topology import Shape
from .values import Number


def _require_shape(value: object, name: str) -> Shape:
    if not isinstance(value, Shape):
        raise TypeError(f"{name} expects Shape")
    return value


def to_brep(shape: Shape, path: str | PathLike[str], /) -> None:
    """Materialize and write a typed Shape at an explicit file boundary."""

    _require_shape(shape, "to_brep")
    resolved_path = str(Path(path).expanduser())
    if not write_brep(shape.native(), resolved_path):
        raise OSError(f"Failed to write BREP file: {resolved_path}")


def from_brep(path: str | PathLike[str], /) -> Shape:
    """Read a BREP snapshot into the selected typed context."""

    resolved_path = str(Path(path).expanduser())
    native = TopoDS_Shape()
    if not read_brep(native, resolved_path):
        raise OSError(f"Failed to read BREP file: {resolved_path}")
    return Shape.from_ocp(native, context=resolve_context())


def to_stl(
    shape: Shape,
    path: str | PathLike[str],
    deflection: Number,
    /,
) -> bool:
    """Write STL from an isolated native snapshot of a typed Shape."""

    _require_shape(shape, "to_stl")
    if (
        isinstance(deflection, bool)
        or not isinstance(deflection, (int, float))
        or not math.isfinite(deflection)
        or deflection <= 0
    ):
        raise ValueError("to_stl deflection must be finite and positive")
    _export_stl(
        ResolvedShape(shape.native()),
        str(Path(path).expanduser()),
        linear_tolerance=float(deflection),
        binary=False,
    )
    return True


def export_stl(
    shape: Shape,
    destination: str | PathLike[str] | BinaryIO,
    *,
    unit: LengthUnit | str = LengthUnit.MILLIMETER,
    linear_tolerance: float = 0.1,
    angular_tolerance: float = 0.5,
    binary: bool = True,
) -> None:
    _require_shape(shape, "export_stl")
    _export_stl(
        ResolvedShape(shape.native()),
        destination,
        unit=unit,
        linear_tolerance=linear_tolerance,
        angular_tolerance=angular_tolerance,
        binary=binary,
    )


def export_step(
    shape: Shape,
    destination: str | PathLike[str] | BinaryIO,
    *,
    unit: LengthUnit | str = LengthUnit.MILLIMETER,
    binary: bool = False,
) -> None:
    _require_shape(shape, "export_step")
    _export_step(
        ResolvedShape(shape.native()),
        destination,
        unit=unit,
        binary=binary,
    )


def export_3mf(
    shape: Shape,
    destination: str | PathLike[str] | BinaryIO,
    *,
    unit: LengthUnit | str = LengthUnit.MILLIMETER,
    linear_tolerance: float = 0.1,
    angular_tolerance: float = 0.5,
    binary: bool = True,
    name: str = "ZenCad object",
    metadata: Mapping[str, str] | None = None,
) -> None:
    _require_shape(shape, "export_3mf")
    _export_3mf(
        ResolvedShape(shape.native()),
        destination,
        unit=unit,
        linear_tolerance=linear_tolerance,
        angular_tolerance=angular_tolerance,
        binary=binary,
        name=name,
        metadata=metadata,
    )


def to_svg_string(
    shape: Shape,
    color: object = (0, 0, 0),
    mapping: bool = False,
) -> str:
    _require_shape(shape, "to_svg_string")
    if not isinstance(mapping, bool):
        raise TypeError("to_svg_string mapping must be bool")
    return str(
        shape_to_svg_string(
            ResolvedShape(shape.native()),
            color,
            mapping,
        )
    )


def to_svg(
    shape: Shape,
    path: str | PathLike[str],
    color: object = (0, 0, 0),
    mapping: bool = False,
) -> None:
    Path(path).expanduser().write_text(
        to_svg_string(shape, color, mapping),
        encoding="utf-8",
    )


def from_svg_string(value: str, /) -> Shape:
    if not isinstance(value, str):
        raise TypeError("from_svg_string expects str")
    legacy = evalcache.unlazy_if_need(SvgReader().read_string(value))
    if not isinstance(legacy, ResolvedShape):
        raise ValueError("SVG import did not produce a Shape")
    return Shape.from_ocp(legacy.Shape(), context=resolve_context())


def from_svg(path: str | PathLike[str], /) -> Shape:
    return from_svg_string(Path(path).expanduser().read_text(encoding="utf-8"))


__all__ = [
    "LengthUnit",
    "export_3mf",
    "export_step",
    "export_stl",
    "from_brep",
    "from_svg",
    "from_svg_string",
    "to_brep",
    "to_stl",
    "to_svg",
    "to_svg_string",
]
