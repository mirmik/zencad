"""Static contracts for process-wide font registration and typed text."""

from typing_extensions import assert_type

from zencad import geom as typed


def text_contract(context: typed.Context) -> None:
    assert_type(context.call(typed.register_font, "font.ttf"), None)
    assert_type(
        context.call(typed.register_font, "font.ttf", typed.FontAspect.REGULAR),
        None,
    )
    assert_type(
        context.call(
            typed.text_to_brep,
            "Hello",
            "Font",
            10.0,
            typed.FontAspect.BOLD,
            composite_curve=True,
        ),
        typed.Compound,
    )
    assert_type(context.call(typed.textshape, "Hello", "Font", 10), typed.Compound)
    assert_type(typed.register_font("font.ttf"), None)
    assert_type(
        typed.text_to_brep(
            "Hello",
            "Font",
            10.0,
            typed.FontAspect.BOLD,
            composite_curve=True,
        ),
        typed.Compound,
    )
    assert_type(typed.textshape("Hello", "Font", 10), typed.Compound)
