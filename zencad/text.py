"""OCP-backed font registration and BREP text construction."""

from pathlib import Path

from OCP.Font import Font_FA_Regular, Font_FA_Undefined, Font_FontMgr
from OCP.NCollection import NCollection_Utf8String
from OCP.StdPrs import StdPrs_BRepFont, StdPrs_BRepTextBuilder
from OCP.TCollection import TCollection_AsciiString


def register_font(font_path, aspect=Font_FA_Undefined):
    """Register a font file with OCCT's process-wide font manager."""
    path = str(Path(font_path).expanduser())
    manager = Font_FontMgr.GetInstance_s()
    font = manager.CheckFont(path)
    if font is None:
        raise FileNotFoundError(f"Font file is not readable by OCCT: {path}")

    if aspect != Font_FA_Undefined:
        font.SetFontPath(aspect, TCollection_AsciiString(path))

    if not manager.RegisterFont(font, True):
        raise RuntimeError(f"OCCT refused to register font: {path}")


def text_to_brep(
    text,
    font_name,
    size,
    aspect=Font_FA_Regular,
    composite_curve=False,
):
    """Build a BREP representation of Unicode text using an OCCT font."""
    font = StdPrs_BRepFont()
    font.SetCompositeCurveMode(composite_curve)
    if not font.FindAndInit(
        TCollection_AsciiString(font_name), aspect, float(size)
    ):
        raise ValueError(f"OCCT could not find or initialize font: {font_name}")

    shape = StdPrs_BRepTextBuilder().Perform(
        font, NCollection_Utf8String(text)
    )
    if shape.IsNull():
        raise ValueError(f"OCCT produced an empty shape for font: {font_name}")
    return shape


__all__ = [
    "Font_FA_Regular",
    "Font_FA_Undefined",
    "register_font",
    "text_to_brep",
]
