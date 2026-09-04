"""Resolved boundary for process-wide font state and BREP text building."""

from __future__ import annotations

import math
from os import PathLike

from OCP.Font import Font_FontAspect

from zencad._native.shape import Shape as ResolvedShape
from zencad.text import register_font as legacy_register_font
from zencad.text import text_to_brep as legacy_text_to_brep


_FONT_ASPECTS = {
    "undefined": Font_FontAspect.Font_FontAspect_UNDEFINED,
    "regular": Font_FontAspect.Font_FontAspect_Regular,
    "bold": Font_FontAspect.Font_FontAspect_Bold,
    "italic": Font_FontAspect.Font_FontAspect_Italic,
    "bold_italic": Font_FontAspect.Font_FontAspect_BoldItalic,
}


def _font_aspect(value: str) -> Font_FontAspect:
    try:
        return _FONT_ASPECTS[value]
    except KeyError as exception:
        raise ValueError(f"unsupported font aspect: {value!r}") from exception


def register_font(
    font_path: str | PathLike[str],
    aspect: str,
) -> None:
    legacy_register_font(font_path, _font_aspect(aspect))


def text_to_brep(
    text: str,
    font_name: str,
    size: float,
    aspect: str,
    composite_curve: bool,
) -> ResolvedShape:
    if not math.isfinite(size) or size <= 0:
        raise ValueError("text size must be finite and positive")
    native = legacy_text_to_brep(
        text,
        font_name,
        size,
        aspect=_font_aspect(aspect),
        composite_curve=composite_curve,
    )
    return ResolvedShape(native)
