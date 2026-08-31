"""Private proving ground for ZenCad's future typed domain API.

Nothing in this package is re-exported from :mod:`zencad` yet.
"""

from .bounds import BoundaryBox, BoundaryBoxRecord
from .curves import Curve, Curve2, CurveKind
from .exttrans import MultiTransform
from .meshes import MeshArrayRecord, MeshData, MeshDataRecord
from .records import (
    CircleParameters,
    CurveProjection,
    EllipseParameters,
    Interval,
    LineParameters,
    ShapeProperties,
)
from .runtime import Runtime
from .sweeps import PipeTransition, PipeTrihedron
from .surfaces import (
    Surface,
    SweepLocationLaw,
    SweepScaleLaw,
    SweepSectionLaw,
    SweepTrihedron,
)
from .text import FontAspect
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
from .transforms import AffineTransform, GeneralTransformation, Quaternion, Transform
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
from .wire_builder import WireBuilder, wire_builder

__all__ = [
    "Compound",
    "CompSolid",
    "AffineTransform",
    "BoundaryBox",
    "BoundaryBoxRecord",
    "Curve",
    "Curve2",
    "CurveKind",
    "CurveProjection",
    "DeferredSequence",
    "Edge",
    "Face",
    "FontAspect",
    "GeneralTransformation",
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
    "PipeTransition",
    "PipeTrihedron",
    "Quaternion",
    "Runtime",
    "Scalar",
    "Shape",
    "ShapeKind",
    "ShapeProperties",
    "Shell",
    "Solid",
    "Surface",
    "SweepLocationLaw",
    "SweepScaleLaw",
    "SweepSectionLaw",
    "SweepTrihedron",
    "Transform",
    "Vector2",
    "Vector3",
    "Vertex",
    "Wire",
    "WireBuilder",
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
    "wire_builder",
]
