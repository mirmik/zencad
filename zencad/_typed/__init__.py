"""Private proving ground for ZenCad's future typed domain API.

Nothing in this package is re-exported from :mod:`zencad` yet.
"""

from .bounds import BoundaryBox, BoundaryBoxRecord
from .curves import Curve, Curve2, CurveKind
from .exttrans import MultiTransform
from .meshes import MeshArrayRecord, MeshData, MeshDataRecord
from .records import (
    CircleParameters,
    EllipseParameters,
    Interval,
    LineParameters,
    ShapeProperties,
)
from .runtime import Runtime
from .surfaces import Surface, SweepTrihedron
from .topology import (
    Compound,
    CompSolid,
    DeferredSequence,
    Edge,
    Face,
    Shape,
    ShapeKind,
    Shell,
    Solid,
    Vertex,
    Wire,
)
from .transforms import Quaternion, Transform
from .values import (
    Point2,
    Point3,
    Scalar,
    Vector2,
    Vector3,
    acos,
    asin,
    atan,
    atan2,
    cos,
    exp,
    log,
    sin,
    sqrt,
    tan,
)

__all__ = [
    "Compound",
    "CompSolid",
    "BoundaryBox",
    "BoundaryBoxRecord",
    "Curve",
    "Curve2",
    "CurveKind",
    "DeferredSequence",
    "Edge",
    "Face",
    "Interval",
    "LineParameters",
    "CircleParameters",
    "EllipseParameters",
    "MeshArrayRecord",
    "MeshData",
    "MeshDataRecord",
    "MultiTransform",
    "Point2",
    "Point3",
    "Quaternion",
    "Runtime",
    "Scalar",
    "Shape",
    "ShapeKind",
    "ShapeProperties",
    "Shell",
    "Solid",
    "Surface",
    "SweepTrihedron",
    "Transform",
    "Vector2",
    "Vector3",
    "Vertex",
    "Wire",
    "acos",
    "asin",
    "atan",
    "atan2",
    "cos",
    "exp",
    "log",
    "sin",
    "sqrt",
    "tan",
]
