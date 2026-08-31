"""Explicit option values for typed topology sweep operations."""

from enum import Enum


class PipeTrihedron(Enum):
    """OCCT trihedron modes supported by the pipe builder."""

    CORRECTED_FRENET = "corrected_frenet"
    FIXED = "fixed"
    FRENET = "frenet"
    CONSTANT_NORMAL = "constant_normal"
    DARBOUX = "darboux"
    GUIDE_AC = "guide_ac"
    GUIDE_PLAN = "guide_plan"
    GUIDE_AC_WITH_CONTACT = "guide_ac_with_contact"
    GUIDE_PLAN_WITH_CONTACT = "guide_plan_with_contact"
    DISCRETE = "discrete_trihedron"


class PipeTransition(Enum):
    """Corner transition policy for a multi-section pipe shell."""

    TRANSFORMED = 0
    RIGHT_CORNER = 1
    ROUND_CORNER = 2
