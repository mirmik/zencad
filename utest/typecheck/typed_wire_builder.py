"""Static result contract for typed WireBuilder authoring."""

from typing_extensions import assert_type

from zencad import _typed as typed


def wire_builder_contract(runtime: typed.Runtime) -> None:
    builder = assert_type(runtime.wire_builder(defrel=True), typed.WireBuilder)
    assert_type(builder.restart(0, 0), typed.WireBuilder)
    assert_type(builder.segment((1, 0)), typed.WireBuilder)
    assert_type(builder.line(0, 1), typed.WireBuilder)
    assert_type(builder.l((-1, 0)), typed.WireBuilder)
    assert_type(builder.arc_by_points((1, 1), (2, 0)), typed.WireBuilder)
    assert_type(builder.arc((0, 0), 2, 1), typed.WireBuilder)
    assert_type(builder.elliptic_arc((0, 0), 3, 2, 1, 0), typed.WireBuilder)
    assert_type(builder.interpolate(((1, 1), (2, 0))), typed.WireBuilder)
    assert_type(builder.close(), typed.WireBuilder)
    assert_type(builder.svg_circle_arc(2, 0, False, True, 2, 2), typed.WireBuilder)
    assert_type(
        builder.svg_elliptic_arc(3, 2, 0, False, True, 2, 2),
        typed.WireBuilder,
    )
    assert_type(builder.plane_circle_arc(2, 1, False, True, 2, 2), typed.WireBuilder)
    assert_type(builder.build(), typed.Wire)
    assert_type(builder.doit(), typed.Wire)
    assert_type(typed.WireBuilder(runtime.point3(0, 0, 0)), typed.WireBuilder)
    assert_type(typed.wire_builder(runtime=runtime), typed.WireBuilder)
