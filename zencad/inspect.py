"""Versioned, headless inspection reports for managed ZenCad scenes."""

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable

from zencad.runtime.script_evaluator import (
    AnimatedScriptError,
    MissingSceneError,
    ScriptExecutionError,
    ScriptTimeoutError,
    evaluate_static_script,
)


INSPECTION_SCHEMA = "zencad.inspect"
INSPECTION_SCHEMA_VERSION = 1


class InspectionError(RuntimeError):
    """Base class for inspection failures outside the model script."""


class GeometryInspectionError(InspectionError):
    """A scene object could not be decoded or measured."""

    def __init__(self, object_id: str, message: str):
        self.object_id = object_id
        super().__init__(f"Could not inspect {object_id!r}: {message}")


@dataclass(frozen=True, slots=True)
class InspectionObject:
    object_id: str
    name: str | None
    kind: str
    visible: bool
    presentation: Mapping[str, Any]
    geometry: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.object_id,
            "name": self.name,
            "kind": self.kind,
            "visible": self.visible,
            "presentation": _plain(self.presentation),
            "geometry": _plain(self.geometry),
        }


@dataclass(frozen=True, slots=True)
class InspectionReport:
    objects: tuple[InspectionObject, ...]
    script_path: str | None = None
    metadata: Mapping[str, Any] | None = None
    schema_version: int = INSPECTION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        visible_count = sum(item.visible for item in self.objects)
        return {
            "schema": INSPECTION_SCHEMA,
            "schema_version": self.schema_version,
            "status": "ok",
            "script": (
                None if self.script_path is None
                else {"path": self.script_path}
            ),
            "scene": {
                "object_count": len(self.objects),
                "visible_object_count": visible_count,
                "metadata": _plain(self.metadata or {}),
            },
            "objects": [item.to_dict() for item in self.objects],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return _json_text(self.to_dict(), indent=indent)


def _plain(value):
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _json_text(value, *, indent=2):
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    ) + "\n"


def _vector(value, size, name):
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ValueError(f"{name} must contain {size} numbers")
    if any(
        isinstance(component, bool) or not isinstance(component, Real)
        for component in value
    ):
        raise ValueError(f"{name} must contain {size} numbers")
    result = tuple(float(component) for component in value)
    if any(not math.isfinite(component) for component in result):
        raise ValueError(f"{name} must contain finite numbers")
    return result


def _rgba(value, default, name):
    if value is None:
        value = default
    result = _vector(value, 4, name)
    if any(not 0 <= component <= 1 for component in result):
        raise ValueError(f"{name} components must be between 0 and 1")
    return result


def _transform_state(properties):
    raw = properties.get("transform") or {
        "scale": 1.0,
        "rotation": (0, 0, 0, 1),
        "translation": (0, 0, 0),
    }
    if not isinstance(raw, Mapping):
        raise ValueError("transform must be an object")
    scale = float(raw.get("scale", 1.0))
    if not math.isfinite(scale) or scale == 0:
        raise ValueError("transform scale must be finite and non-zero")
    rotation = _vector(
        raw.get("rotation", (0, 0, 0, 1)), 4, "transform rotation"
    )
    if not any(rotation):
        raise ValueError("transform rotation quaternion must be non-zero")
    translation = _vector(
        raw.get("translation", (0, 0, 0)), 3, "transform translation"
    )
    return {
        "scale": scale,
        "rotation": rotation,
        "translation": translation,
    }


def _transformation(state):
    from OCP.gp import gp_Quaternion, gp_Trsf, gp_Vec

    value = gp_Trsf()
    value.SetRotation(gp_Quaternion(*state["rotation"]))
    value.SetScaleFactor(state["scale"])
    value.SetTranslationPart(gp_Vec(*state["translation"]))
    return value


def _presentation(record):
    properties = record.properties
    visible = properties.get("visible", True)
    if not isinstance(visible, bool):
        raise ValueError("visible must be a boolean")
    name = properties.get("name")
    if name is not None and (not isinstance(name, str) or not name):
        raise ValueError("name must be a non-empty string")
    presentation = {
        "color": _rgba(
            properties.get("color"), (0.6, 0.6, 0.8, 0), "color"
        ),
        "border_color": _rgba(
            properties.get("border_color"), (0, 0, 0, 0), "border_color"
        ),
        "wire_color": _rgba(
            properties.get("wire_color"), (0, 0, 0, 0), "wire_color"
        ),
        "transform": _transform_state(properties),
    }
    if record.kind == "mesh":
        from zencad._native.mesh import normalize_mesh_display_mode

        presentation["display_mode"] = normalize_mesh_display_mode(
            properties.get("display_mode")
        )
    return name, visible, presentation


def _bbox(coordinates):
    if coordinates is None:
        return None
    xmin, ymin, zmin, xmax, ymax, zmax = coordinates
    minimum = [float(xmin), float(ymin), float(zmin)]
    maximum = [float(xmax), float(ymax), float(zmax)]
    size = [maximum[index] - minimum[index] for index in range(3)]
    center = [
        (minimum[index] + maximum[index]) / 2 for index in range(3)
    ]
    return {
        "min": minimum,
        "max": maximum,
        "size": size,
        "center": center,
    }


def _shape_bbox(shape):
    from OCP.Bnd import Bnd_Box
    from zencad.occ_compat import add_to_bounds

    bounds = Bnd_Box()
    add_to_bounds(shape, bounds)
    return None if bounds.IsVoid() else bounds.Get()


def _topology_counts(shape):
    from OCP.TopAbs import (
        TopAbs_COMPOUND,
        TopAbs_COMPSOLID,
        TopAbs_EDGE,
        TopAbs_FACE,
        TopAbs_SHELL,
        TopAbs_SOLID,
        TopAbs_VERTEX,
        TopAbs_WIRE,
    )
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape

    kinds = (
        ("vertices", TopAbs_VERTEX),
        ("edges", TopAbs_EDGE),
        ("wires", TopAbs_WIRE),
        ("faces", TopAbs_FACE),
        ("shells", TopAbs_SHELL),
        ("solids", TopAbs_SOLID),
        ("compsolids", TopAbs_COMPSOLID),
        ("compounds", TopAbs_COMPOUND),
    )
    result = {}
    for name, kind in kinds:
        values = TopTools_IndexedMapOfShape()
        TopExp.MapShapes_s(shape, kind, values)
        result[name] = values.Extent()
    return result


def _point_tuple(value):
    return [float(value.X()), float(value.Y()), float(value.Z())]


def _inspect_brep(record, transform):
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.GProp import GProp_GProps
    from zencad._native.shape import Shape
    from zencad.occ_compat import surface_properties, volume_properties
    from zencad.runtime.scene_protocol import decode_brep

    source = decode_brep(record.payload)
    transformed = BRepBuilderAPI_Transform(source, transform, True).Shape()
    shape = Shape(transformed)
    topology = _topology_counts(transformed)
    validation = shape.validate().to_dict()

    surface_area = None
    surface_center = None
    if topology["faces"]:
        surface = GProp_GProps()
        surface_properties(transformed, surface)
        surface_area = float(surface.Mass())
        surface_center = _point_tuple(surface.CentreOfMass())

    volume = None
    volume_center = None
    if topology["solids"]:
        volume_properties_value = GProp_GProps()
        volume_properties(transformed, volume_properties_value)
        volume = float(volume_properties_value.Mass())
        volume_center = _point_tuple(volume_properties_value.CentreOfMass())

    return {
        "payload_sha256": hashlib.sha256(record.payload).hexdigest(),
        "shape_type": shape.shapetype() or "shape",
        "bbox": _bbox(_shape_bbox(transformed)),
        "volume": volume,
        "volume_center": volume_center,
        "surface_area": surface_area,
        "surface_center": surface_center,
        "topology": topology,
        "valid": bool(validation["valid"]),
        "validation": validation,
    }


def _transformed_points(points, transform):
    from OCP.gp import gp_Pnt

    result = []
    for point in points:
        value = gp_Pnt(*point).Transformed(transform)
        result.append((float(value.X()), float(value.Y()), float(value.Z())))
    return tuple(result)


def _points_bbox(points):
    if not points:
        return None
    axes = tuple(zip(*points))
    return (
        min(axes[0]), min(axes[1]), min(axes[2]),
        max(axes[0]), max(axes[1]), max(axes[2]),
    )


def _triangle_area(first, second, third):
    left = tuple(second[index] - first[index] for index in range(3))
    right = tuple(third[index] - first[index] for index in range(3))
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return math.sqrt(sum(component * component for component in cross)) / 2


def _inspect_mesh(record, transform):
    from zencad.runtime.scene_protocol import decode_mesh

    mesh = decode_mesh(record.payload)
    positions = _transformed_points(mesh.positions, transform)
    triangle_areas = tuple(
        _triangle_area(*(positions[index] for index in triangle))
        for triangle in mesh.triangles
    )
    degenerate_count = sum(area <= 1e-15 for area in triangle_areas)
    return {
        "payload_sha256": hashlib.sha256(record.payload).hexdigest(),
        "mesh_type": "triangles",
        "bbox": _bbox(_points_bbox(positions)),
        "vertex_count": len(positions),
        "triangle_count": len(mesh.triangles),
        "surface_area": float(sum(triangle_areas)),
        "degenerate_triangle_count": degenerate_count,
        "valid": degenerate_count == 0,
    }


def _inspect_point(record, transform):
    from zencad.runtime.scene_protocol import decode_json_payload

    source = _vector(decode_json_payload(record.payload), 3, "point")
    point = _transformed_points((source,), transform)[0]
    coordinates = tuple(point) + tuple(point)
    return {
        "payload_sha256": hashlib.sha256(record.payload).hexdigest(),
        "coordinates": list(point),
        "bbox": _bbox(coordinates),
        "valid": True,
    }


def _inspect_line(record, transform):
    from zencad.runtime.scene_protocol import decode_json_payload

    source = decode_json_payload(record.payload)
    if not isinstance(source, Mapping):
        raise ValueError("line payload must be an object")
    start = _vector(source.get("start"), 3, "line start")
    end = _vector(source.get("end"), 3, "line end")
    start, end = _transformed_points((start, end), transform)
    length = math.sqrt(sum(
        (end[index] - start[index]) ** 2 for index in range(3)
    ))
    return {
        "payload_sha256": hashlib.sha256(record.payload).hexdigest(),
        "start": list(start),
        "end": list(end),
        "length": length,
        "bbox": _bbox(_points_bbox((start, end))),
        "valid": math.isfinite(length) and length > 0,
    }


def inspect_snapshot(snapshot, *, script_path=None) -> InspectionReport:
    """Describe a scene snapshot without constructing Qt or AIS objects."""
    from zencad.runtime.scene_protocol import SceneSnapshot

    if not isinstance(snapshot, SceneSnapshot):
        raise TypeError("inspect_snapshot requires a SceneSnapshot")
    inspectors = {
        "brep": _inspect_brep,
        "mesh": _inspect_mesh,
        "point": _inspect_point,
        "line": _inspect_line,
    }
    objects = []
    for record in snapshot.objects:
        try:
            name, visible, presentation = _presentation(record)
            inspector = inspectors.get(record.kind)
            if inspector is None:
                raise ValueError(f"unsupported scene object kind {record.kind!r}")
            geometry = inspector(
                record,
                _transformation(presentation["transform"]),
            )
            objects.append(InspectionObject(
                object_id=record.object_id,
                name=name,
                kind=record.kind,
                visible=visible,
                presentation=presentation,
                geometry=geometry,
            ))
        except GeometryInspectionError:
            raise
        except Exception as exception:
            raise GeometryInspectionError(
                record.object_id, str(exception) or type(exception).__name__
            ) from exception
    return InspectionReport(
        objects=tuple(objects),
        script_path=(
            None if script_path is None
            else str(Path(script_path).expanduser().resolve())
        ),
        metadata=snapshot.metadata,
    )


def inspect_script(
    script_path,
    *,
    timeout=30,
    arguments=(),
    output: Callable[[str, str], None] | None = None,
) -> InspectionReport:
    """Evaluate a script in isolation and return its inspection report."""
    script = Path(script_path).expanduser().resolve()
    result = evaluate_static_script(
        script,
        arguments=arguments,
        timeout=timeout,
        output=output,
    )
    return inspect_snapshot(result.snapshot, script_path=script)


def inspection_error_report(
    script_path,
    code,
    message,
    *,
    exception_type=None,
    traceback_text=None,
    details=None,
):
    """Build a versioned JSON-ready terminal error report."""
    error = {"code": code, "message": str(message)}
    if exception_type:
        error["exception_type"] = str(exception_type)
    if traceback_text:
        error["traceback"] = str(traceback_text)
    if details:
        error["details"] = _plain(details)
    return {
        "schema": INSPECTION_SCHEMA,
        "schema_version": INSPECTION_SCHEMA_VERSION,
        "status": "error",
        "script": {
            "path": str(Path(script_path).expanduser().resolve())
        },
        "error": error,
    }


def _write_report(path, text):
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.",
        suffix=".json",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def _human_report(report):
    lines = [
        f"ZenCad inspection v{report.schema_version}",
        f"objects: {len(report.objects)} "
        f"({sum(item.visible for item in report.objects)} visible)",
    ]
    for item in report.objects:
        geometry = item.geometry
        subtype = geometry.get("shape_type") or geometry.get("mesh_type")
        state = "valid" if geometry.get("valid") else "invalid"
        lines.append(
            f"- {item.object_id}: {item.kind}"
            f"/{subtype or 'object'} {state}"
            f"{' visible' if item.visible else ' hidden'}"
        )
        bounds = geometry.get("bbox")
        if bounds is not None:
            lines.append("  bbox size: " + ", ".join(
                f"{value:.9g}" for value in bounds["size"]
            ))
        if geometry.get("volume") is not None:
            lines.append(f"  volume: {geometry['volume']:.12g}")
        if geometry.get("surface_area") is not None:
            lines.append(f"  surface area: {geometry['surface_area']:.12g}")
    return "\n".join(lines)


def _argument_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="zencad inspect",
        description="Inspect a ZenCad model without opening a GUI.",
    )
    parser.add_argument("script", help="ZenCad Python script")
    parser.add_argument(
        "--json", action="store_true", help="write the report to stdout as JSON"
    )
    parser.add_argument(
        "-o", "--output", help="atomically write the JSON report to this file"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="script evaluation timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "script_arguments",
        nargs="*",
        help="arguments passed to the model script (put them after --)",
    )
    return parser


def _emit_cli_report(arguments, payload, *, human=None, error=False):
    text = _json_text(payload)
    if arguments.output:
        _write_report(arguments.output, text)
    if arguments.json:
        sys.stdout.write(text)
    elif not arguments.output and human:
        print(human, file=sys.stderr if error else sys.stdout)


def inspect_cli(argv=None):
    """Command-line adapter. Returns a stable process exit code."""
    parser = _argument_parser()
    arguments = parser.parse_args(argv)

    def script_output(_stream, text):
        sys.stderr.write(text)
        sys.stderr.flush()

    try:
        report = inspect_script(
            arguments.script,
            timeout=arguments.timeout,
            arguments=arguments.script_arguments,
            output=script_output,
        )
        try:
            _emit_cli_report(
                arguments,
                report.to_dict(),
                human=_human_report(report),
            )
        except OSError as exception:
            print(
                f"zencad inspect: could not write report: {exception}",
                file=sys.stderr,
            )
            return 6
        return 0
    except ScriptExecutionError as exception:
        error = inspection_error_report(
            arguments.script,
            "script_error",
            exception.payload.get("message") or str(exception),
            exception_type=exception.payload.get("exception_type"),
            traceback_text=exception.payload.get("traceback"),
            details={"kind": exception.payload.get("kind")},
        )
        exit_code = 3
    except AnimatedScriptError as exception:
        error = inspection_error_report(
            arguments.script, "animated_script", str(exception)
        )
        exit_code = 3
    except (MissingSceneError, GeometryInspectionError) as exception:
        details = (
            {"object_id": exception.object_id}
            if isinstance(exception, GeometryInspectionError)
            else None
        )
        error = inspection_error_report(
            arguments.script,
            "geometry_error" if details else "missing_scene",
            str(exception),
            details=details,
        )
        exit_code = 4
    except ScriptTimeoutError as exception:
        error = inspection_error_report(
            arguments.script,
            "timeout",
            str(exception),
            details={"timeout_seconds": exception.timeout},
        )
        exit_code = 5
    except (FileNotFoundError, TypeError, ValueError) as exception:
        parser.error(str(exception))

    try:
        _emit_cli_report(
            arguments,
            error,
            human=f"zencad inspect: {error['error']['message']}",
            error=True,
        )
    except OSError as exception:
        print(f"zencad inspect: could not write report: {exception}", file=sys.stderr)
        return 6
    return exit_code


__all__ = [
    "INSPECTION_SCHEMA",
    "INSPECTION_SCHEMA_VERSION",
    "GeometryInspectionError",
    "InspectionError",
    "InspectionObject",
    "InspectionReport",
    "inspect_script",
    "inspect_snapshot",
    "inspection_error_report",
]
