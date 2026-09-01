"""Static contracts for process-wide font registration and typed text."""

from typing_extensions import assert_type

from zencad import _typed as typed


def text_contract(runtime: typed.Runtime) -> None:
    assert_type(runtime.register_font("font.ttf"), None)
    assert_type(
        runtime.register_font("font.ttf", typed.FontAspect.REGULAR),
        None,
    )
    assert_type(
        runtime.text_to_brep(
            "Hello",
            "Font",
            runtime.box(2).mass(),
            typed.FontAspect.BOLD,
            composite_curve=True,
        ),
        typed.Compound,
    )
    assert_type(runtime.textshape("Hello", "Font", 10), typed.Compound)
    assert_type(typed.register_font("font.ttf"), None)
    assert_type(
        typed.text_to_brep(
            "Hello",
            "Font",
            runtime.box(2).mass(),
            typed.FontAspect.BOLD,
            composite_curve=True,
        ),
        typed.Compound,
    )
    assert_type(typed.textshape("Hello", "Font", 10), typed.Compound)
