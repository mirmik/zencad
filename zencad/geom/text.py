"""Typed text operations without exposing mutable OCCT font objects."""

from __future__ import annotations

from enum import Enum
from os import PathLike

from zencad.operation import operation

from . import _text_operations as text_ops
from .topology import COMPOUND_SPEC, Compound


class FontAspect(Enum):
    """Font style requested from OCCT's process-wide font manager."""

    UNDEFINED = "undefined"
    REGULAR = "regular"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"


def _require_font_aspect(value: object, name: str) -> FontAspect:
    if not isinstance(value, FontAspect):
        raise TypeError(f"{name} must be FontAspect")
    return value


def register_font(
    font_path: str | PathLike[str],
    aspect: FontAspect = FontAspect.UNDEFINED,
) -> None:
    """Immediately register a font in OCCT's process-wide font manager."""

    if not isinstance(font_path, (str, PathLike)):
        raise TypeError("register_font path must be str or PathLike")
    resolved_aspect = _require_font_aspect(aspect, "register_font aspect")
    text_ops.register_font(font_path, resolved_aspect.value)


@operation(
    result=COMPOUND_SPEC,
    returns=Compound,
    operation_id="zencad.typed.text_to_brep",
    operation_version="1",
    cacheable=False,
)
def text_to_brep(
    text: str,
    font_name: str,
    size: float,
    aspect: FontAspect = FontAspect.REGULAR,
    composite_curve: bool = False,
) -> Compound:
    if not isinstance(text, str):
        raise TypeError("text_to_brep text must be str")
    if not isinstance(font_name, str):
        raise TypeError("text_to_brep font_name must be str")
    resolved_aspect = _require_font_aspect(aspect, "text_to_brep aspect")
    if not isinstance(composite_curve, bool):
        raise TypeError("text_to_brep composite_curve must be bool")
    return Compound(
        text_ops.text_to_brep(
            text,
            font_name,
            float(size),
            resolved_aspect.value,
            composite_curve,
        )
    )


def textshape(
    text: str,
    fontname: str,
    size: float,
    composite_curve: bool = False,
) -> Compound:
    """Legacy spelling for :func:`text_to_brep`."""

    return text_to_brep(
        text,
        fontname,
        size,
        FontAspect.REGULAR,
        composite_curve,
    )


__all__ = ["FontAspect", "register_font", "text_to_brep", "textshape"]
