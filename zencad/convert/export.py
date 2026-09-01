"""Explicit headless CAD export boundaries shared by legacy and typed APIs."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
import io
import math
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from typing import BinaryIO
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZIP_DEFLATED, ZipFile

import evalcache
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy, BRepBuilderAPI_Transform
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.STEPControl import (
    STEPControl_AsIs,
    STEPControl_Controller,
    STEPControl_Writer,
)
from OCP.StlAPI import StlAPI_Writer
from OCP.gp import gp_Pnt, gp_Trsf

from zencad.geom.mesh import to_mesh
from zencad.geom.shape import Shape
from zencad.geom.validation import ShapeValidationError, _validate


class LengthUnit(str, Enum):
    MICRON = "micron"
    MILLIMETER = "millimeter"
    CENTIMETER = "centimeter"
    METER = "meter"
    INCH = "inch"
    FOOT = "foot"


_UNIT_ALIASES = {
    "um": LengthUnit.MICRON,
    "micron": LengthUnit.MICRON,
    "mm": LengthUnit.MILLIMETER,
    "millimeter": LengthUnit.MILLIMETER,
    "cm": LengthUnit.CENTIMETER,
    "centimeter": LengthUnit.CENTIMETER,
    "m": LengthUnit.METER,
    "meter": LengthUnit.METER,
    "in": LengthUnit.INCH,
    "inch": LengthUnit.INCH,
    "ft": LengthUnit.FOOT,
    "foot": LengthUnit.FOOT,
}
_MILLIMETERS_PER_UNIT = {
    LengthUnit.MICRON: 0.001,
    LengthUnit.MILLIMETER: 1.0,
    LengthUnit.CENTIMETER: 10.0,
    LengthUnit.METER: 1000.0,
    LengthUnit.INCH: 25.4,
    LengthUnit.FOOT: 304.8,
}
_STEP_UNITS = {
    LengthUnit.MICRON: "UM",
    LengthUnit.MILLIMETER: "MM",
    LengthUnit.CENTIMETER: "CM",
    LengthUnit.METER: "M",
    LengthUnit.INCH: "INCH",
    LengthUnit.FOOT: "FT",
}
_STEP_LOCK = RLock()


def _unit(value: LengthUnit | str) -> LengthUnit:
    if isinstance(value, LengthUnit):
        return value
    if not isinstance(value, str):
        raise TypeError("export unit must be LengthUnit or str")
    normalized = value.strip().lower()
    try:
        return _UNIT_ALIASES[normalized]
    except KeyError as exception:
        choices = ", ".join(unit.value for unit in LengthUnit)
        raise ValueError(f"unknown export unit {value!r}; expected {choices}") from exception


def _positive(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _shape(value: object, name: str) -> Shape:
    resolved = evalcache.unlazy_if_need(value)
    if not isinstance(resolved, Shape):
        raise TypeError(f"{name} expects Shape")
    report = _validate(resolved)
    if not report.valid:
        raise ShapeValidationError(report)
    return resolved


def _owned_shape(shape: Shape, scale: float = 1.0) -> Shape:
    if scale == 1.0:
        native = BRepBuilderAPI_Copy(shape.Shape()).Shape()
    else:
        transform = gp_Trsf()
        transform.SetScale(gp_Pnt(0, 0, 0), scale)
        native = BRepBuilderAPI_Transform(shape.Shape(), transform, True).Shape()
    if native.IsNull():
        raise ValueError("export could not create an owned shape snapshot")
    return Shape(native)


def _path_or_stream(
    destination: str | PathLike[str] | BinaryIO,
) -> tuple[Path | None, BinaryIO | None]:
    if isinstance(destination, (str, PathLike)):
        return Path(destination).expanduser(), None
    writer = getattr(destination, "write", None)
    if not callable(writer):
        raise TypeError("export destination must be str, PathLike, or binary stream")
    return None, destination


def _write_bytes(
    destination: str | PathLike[str] | BinaryIO,
    payload: bytes,
    format_name: str,
) -> None:
    path, stream = _path_or_stream(destination)
    try:
        if path is not None:
            path.write_bytes(payload)
            return
        assert stream is not None
        written = stream.write(payload)
        if written is not None and written != len(payload):
            raise OSError(f"short write: {written} of {len(payload)} bytes")
    except (OSError, TypeError, ValueError) as exception:
        target = str(path) if path is not None else repr(destination)
        raise OSError(f"failed to write {format_name} to {target}: {exception}") from exception


def export_stl(
    shape: Shape,
    destination: str | PathLike[str] | BinaryIO,
    *,
    unit: LengthUnit | str = LengthUnit.MILLIMETER,
    linear_tolerance: float = 0.1,
    angular_tolerance: float = 0.5,
    binary: bool = True,
) -> None:
    """Export an owned triangulated snapshot as binary or ASCII STL."""

    resolved = _shape(shape, "export_stl")
    resolved_unit = _unit(unit)
    linear = _positive(linear_tolerance, "linear_tolerance")
    angular = _positive(angular_tolerance, "angular_tolerance")
    if not isinstance(binary, bool):
        raise TypeError("binary must be bool")
    owned = _owned_shape(
        resolved,
        1.0 / _MILLIMETERS_PER_UNIT[resolved_unit],
    )
    mesher = BRepMesh_IncrementalMesh(
        owned.Shape(),
        linear,
        False,
        angular,
        True,
    )
    if not mesher.IsDone():
        raise RuntimeError("OCCT failed to triangulate shape for STL export")

    path, stream = _path_or_stream(destination)
    with TemporaryDirectory(prefix="zencad-stl-") as temporary_directory:
        output = path or Path(temporary_directory) / "shape.stl"
        writer = StlAPI_Writer()
        writer.ASCIIMode = not binary
        try:
            written = writer.Write(owned.Shape(), str(output))
        except Exception as exception:
            raise OSError(f"failed to write STL to {output}: {exception}") from exception
        if not written:
            raise OSError(f"failed to write STL to {output}: OCCT writer failed")
        if stream is not None:
            _write_bytes(stream, output.read_bytes(), "STL")


def export_step(
    shape: Shape,
    destination: str | PathLike[str] | BinaryIO,
    *,
    unit: LengthUnit | str = LengthUnit.MILLIMETER,
    binary: bool = False,
) -> None:
    """Export exact BREP geometry as ISO-10303-21 STEP text."""

    resolved = _shape(shape, "export_step")
    resolved_unit = _unit(unit)
    if not isinstance(binary, bool):
        raise TypeError("binary must be bool")
    if binary:
        raise ValueError("STEP export supports ASCII ISO-10303-21 only")

    with _STEP_LOCK:
        STEPControl_Controller.Init_s()
        previous_unit = Interface_Static.CVal_s("write.step.unit")
        if not Interface_Static.SetCVal_s(
            "write.step.unit",
            _STEP_UNITS[resolved_unit],
        ):
            raise RuntimeError(f"OCCT rejected STEP unit {resolved_unit.value!r}")
        try:
            writer = STEPControl_Writer()
            status = writer.Transfer(
                _owned_shape(resolved).Shape(),
                STEPControl_AsIs,
            )
            if status != IFSelect_RetDone:
                raise RuntimeError(f"STEP transfer failed with status {status.name}")
            buffer = io.BytesIO()
            status = writer.WriteStream(buffer)
            if status != IFSelect_RetDone:
                raise OSError(f"STEP writer failed with status {status.name}")
        finally:
            Interface_Static.SetCVal_s("write.step.unit", previous_unit)
    _write_bytes(destination, buffer.getvalue(), "STEP")


def _model_xml(
    shape: Shape,
    unit: LengthUnit,
    linear_tolerance: float,
    angular_tolerance: float,
    name: str,
    metadata: Mapping[str, str],
) -> bytes:
    mesh = to_mesh(
        shape,
        linear_deflection=linear_tolerance,
        angular_deflection=angular_tolerance,
    )
    namespace = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    model = Element(
        "model",
        {
            "unit": unit.value,
            "xml:lang": "en-US",
            "xmlns": namespace,
        },
    )
    for key, value in (("Title", name), *metadata.items()):
        item = SubElement(model, "metadata", {"name": key})
        item.text = value
    resources = SubElement(model, "resources")
    object_node = SubElement(
        resources,
        "object",
        {"id": "1", "type": "model", "name": name},
    )
    mesh_node = SubElement(object_node, "mesh")
    vertices = SubElement(mesh_node, "vertices")
    for x, y, z in mesh.positions:
        SubElement(vertices, "vertex", {"x": repr(x), "y": repr(y), "z": repr(z)})
    triangles = SubElement(mesh_node, "triangles")
    for first, second, third in mesh.triangles:
        SubElement(
            triangles,
            "triangle",
            {"v1": str(first), "v2": str(second), "v3": str(third)},
        )
    build = SubElement(model, "build")
    SubElement(build, "item", {"objectid": "1"})
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(model)


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
    """Export a standards-shaped minimal 3MF model archive."""

    resolved = _shape(shape, "export_3mf")
    resolved_unit = _unit(unit)
    linear = _positive(linear_tolerance, "linear_tolerance")
    angular = _positive(angular_tolerance, "angular_tolerance")
    if not isinstance(binary, bool):
        raise TypeError("binary must be bool")
    if not binary:
        raise ValueError("3MF is a binary ZIP container and has no ASCII mode")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("3MF object name must be a non-empty string")
    normalized_metadata: dict[str, str] = {}
    if metadata is not None:
        if not isinstance(metadata, Mapping):
            raise TypeError("3MF metadata must be a string mapping")
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("3MF metadata keys and values must be strings")
            normalized_metadata[key] = value

    scaled = _owned_shape(
        resolved,
        1.0 / _MILLIMETERS_PER_UNIT[resolved_unit],
    )
    model = _model_xml(
        scaled,
        resolved_unit,
        linear,
        angular,
        name.strip(),
        normalized_metadata,
    )
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/3D/3dmodel.model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            "</Relationships>",
        )
        archive.writestr("3D/3dmodel.model", model)
    _write_bytes(destination, buffer.getvalue(), "3MF")


__all__ = ["LengthUnit", "export_3mf", "export_step", "export_stl"]
