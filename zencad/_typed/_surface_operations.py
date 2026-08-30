"""Resolved operations and immutable snapshots for typed surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math

from OCP.Geom import Geom_CylindricalSurface, Geom_Surface
from OCP.GeomAbs import GeomAbs_C0, GeomAbs_C1, GeomAbs_C2, GeomAbs_C3
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.GeomFill import (
    GeomFill_CorrectedFrenet,
    GeomFill_CurveAndTrihedron,
    GeomFill_EvolvedSection,
    GeomFill_Frenet,
    GeomFill_Location,
    GeomFill_Sweep,
)
from OCP.GeomLProp import GeomLProp_SLProps
from OCP.GeomTools import GeomTools_SurfaceSet
from OCP.Law import Law_Constant
from OCP.gp import gp_Ax3, gp_Dir, gp_Pnt

from ._curve_operations import (
    CurveValue,
    curve_from_ocp,
    curve_to_ocp,
)
from ._value_operations import Point3Value, Vector3Value


@dataclass(frozen=True, slots=True)
class SurfaceValue:
    """Immutable full-precision OCCT snapshot of a parametric surface."""

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes) or not self.data:
            raise TypeError("SurfaceValue data must be non-empty bytes")

    def __evalcache_key__(self) -> bytes:
        return b"zencad-surface-value-v1\x00" + self.data


def surface_from_ocp(value: Geom_Surface) -> SurfaceValue:
    if not isinstance(value, Geom_Surface):
        raise TypeError("surface_from_ocp expects Geom_Surface")
    surfaces = GeomTools_SurfaceSet()
    surfaces.Add(value)
    stream = BytesIO()
    surfaces.Write(stream)
    data = stream.getvalue()
    if not data:
        raise ValueError("OCCT produced an empty Surface serialization")
    return SurfaceValue(data)


def surface_to_ocp(value: SurfaceValue) -> Geom_Surface:
    if not isinstance(value, SurfaceValue):
        raise TypeError("surface_to_ocp expects SurfaceValue")
    surfaces = GeomTools_SurfaceSet()
    surfaces.Read(BytesIO(value.data))
    surface = surfaces.Surface(1)
    if not isinstance(surface, Geom_Surface):
        raise ValueError("invalid OCCT Surface serialization")
    return surface


def valid_surface(value: SurfaceValue) -> bool:
    try:
        surface_to_ocp(value)
    except (TypeError, ValueError, RuntimeError):
        return False
    return True


def _positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive scalar")
    return value


def cylinder_surface(radius: float) -> SurfaceValue:
    radius = _positive(radius, "cylinder surface radius")
    native = Geom_CylindricalSurface(
        gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        radius,
    )
    return surface_from_ocp(native)


_CONTINUITY = {
    0: GeomAbs_C0,
    1: GeomAbs_C1,
    2: GeomAbs_C2,
    3: GeomAbs_C3,
}


def sweep_surface(
    section: CurveValue,
    spine: CurveValue,
    scale: float,
    trihedron: str,
    tolerance: float,
    continuity: int,
    max_degree: int,
    max_segments: int,
) -> SurfaceValue:
    """Materialize the representative constant-scale sweep-law chain."""
    scale = _positive(scale, "sweep surface scale")
    tolerance = _positive(tolerance, "sweep surface tolerance")
    if continuity not in _CONTINUITY:
        raise ValueError("sweep surface continuity must be between 0 and 3")
    if max_degree <= 0:
        raise ValueError("sweep surface max_degree must be positive")
    if max_segments <= 0:
        raise ValueError("sweep surface max_segments must be positive")

    section_curve = curve_to_ocp(section)
    spine_curve = curve_to_ocp(spine)
    scaling = Law_Constant()
    scaling.Set(
        scale,
        spine_curve.FirstParameter(),
        spine_curve.LastParameter(),
    )
    section_law = GeomFill_EvolvedSection(section_curve, scaling)

    if trihedron == "corrected_frenet":
        trihedron_law = GeomFill_CorrectedFrenet()
    elif trihedron == "frenet":
        trihedron_law = GeomFill_Frenet()
    else:
        raise ValueError(f"unsupported sweep trihedron: {trihedron!r}")
    location_law = GeomFill_CurveAndTrihedron(trihedron_law)
    if not location_law.SetCurve(GeomAdaptor_Curve(spine_curve)):
        raise ValueError("cannot initialize sweep location law from spine")

    sweep = GeomFill_Sweep(location_law)
    sweep.SetTolerance(tolerance)
    sweep.Build(
        section_law,
        GeomFill_Location,
        _CONTINUITY[continuity],
        max_degree,
        max_segments,
    )
    return surface_from_ocp(sweep.Surface())


def surface_point(value: SurfaceValue, u: float, v: float) -> Point3Value:
    point = surface_to_ocp(value).Value(u, v)
    return Point3Value(float(point.X()), float(point.Y()), float(point.Z()))


def surface_normal(value: SurfaceValue, u: float, v: float) -> Vector3Value:
    properties = GeomLProp_SLProps(surface_to_ocp(value), u, v, 1, 1e-9)
    if not properties.IsNormalDefined():
        raise ValueError("surface normal is undefined at the requested parameters")
    normal = properties.Normal()
    return Vector3Value(float(normal.X()), float(normal.Y()), float(normal.Z()))


def surface_bound(value: SurfaceValue, index: int) -> float:
    if index not in (0, 1, 2, 3):
        raise ValueError("surface bound index must be between 0 and 3")
    return float(surface_to_ocp(value).Bounds()[index])


def surface_u_iso(value: SurfaceValue, parameter: float) -> CurveValue:
    return curve_from_ocp(surface_to_ocp(value).UIso(parameter))


def surface_v_iso(value: SurfaceValue, parameter: float) -> CurveValue:
    return curve_from_ocp(surface_to_ocp(value).VIso(parameter))
