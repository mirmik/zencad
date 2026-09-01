"""Canonical planar curve domain type and constructors."""

from .curve_constructors import ellipse2, segment2, trim_curve2
from .curves import Curve2

__all__ = ["Curve2", "ellipse2", "segment2", "trim_curve2"]
