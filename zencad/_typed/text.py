"""Typed text-domain options without exposing mutable OCCT font objects."""

from enum import Enum


class FontAspect(Enum):
    """Font style requested from OCCT's process-wide font manager."""

    UNDEFINED = "undefined"
    REGULAR = "regular"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
