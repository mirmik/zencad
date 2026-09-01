"""Public criteria used by typed topology selectors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import ClassVar


Coordinates3 = tuple[float, float, float]


class Axis(Enum):
    """Principal coordinate axes accepted by topology selectors."""

    X = (1.0, 0.0, 0.0)
    Y = (0.0, 1.0, 0.0)
    Z = (0.0, 0.0, 1.0)

    @property
    def direction(self) -> Coordinates3:
        return self.value


class GeomType(Enum):
    """Stable geometry categories returned by :meth:`ShapeList.group_by`."""

    VERTEX = "vertex"
    LINE = "line"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    HYPERBOLA = "hyperbola"
    PARABOLA = "parabola"
    BEZIER = "bezier"
    BSPLINE = "bspline"
    OFFSET = "offset"
    PLANE = "plane"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    TORUS = "torus"
    EXTRUSION = "extrusion"
    REVOLUTION = "revolution"
    WIRE = "wire"
    SHELL = "shell"
    SOLID = "solid"
    COMPSOLID = "compsolid"
    COMPOUND = "compound"
    OTHER = "other"


def _coordinates(value: object, name: str) -> Coordinates3:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must contain three numeric coordinates")
    try:
        coordinates = tuple(float(item) for item in value)  # type: ignore[union-attr]
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must contain three numeric coordinates") from error
    if len(coordinates) != 3 or not all(math.isfinite(item) for item in coordinates):
        raise ValueError(f"{name} must contain three finite coordinates")
    return coordinates


@dataclass(frozen=True, slots=True)
class Plane:
    """A numeric plane criterion with an origin and a non-zero normal."""

    origin: Coordinates3 = (0.0, 0.0, 0.0)
    normal: Coordinates3 = (0.0, 0.0, 1.0)

    XY: ClassVar[Plane]
    XZ: ClassVar[Plane]
    YZ: ClassVar[Plane]

    def __post_init__(self) -> None:
        origin = _coordinates(self.origin, "Plane origin")
        normal = _coordinates(self.normal, "Plane normal")
        if math.sqrt(sum(item * item for item in normal)) == 0:
            raise ValueError("Plane normal must be non-zero")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "normal", normal)

    @classmethod
    def xy(cls, z: float = 0.0) -> Plane:
        return cls((0.0, 0.0, float(z)), Axis.Z.direction)

    @classmethod
    def xz(cls, y: float = 0.0) -> Plane:
        return cls((0.0, float(y), 0.0), Axis.Y.direction)

    @classmethod
    def yz(cls, x: float = 0.0) -> Plane:
        return cls((float(x), 0.0, 0.0), Axis.X.direction)


Plane.XY = Plane.xy()
Plane.XZ = Plane.xz()
Plane.YZ = Plane.yz()


__all__ = ["Axis", "GeomType", "Plane"]
