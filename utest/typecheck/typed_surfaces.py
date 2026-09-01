"""Static result contract for typed Surface handles and sweep adapters."""

from typing_extensions import assert_type

from zencad import _typed as typed


def surface_contract(context: typed.Context) -> None:
    shape = context.call(typed.box, 2)
    radius = shape.mass() / 4
    cylinder = assert_type(context.call(typed.cylinder_surface, radius), typed.Surface)
    assert_type(typed.cylinder_surface(radius), typed.Surface)
    sweep = assert_type(
        context.call(
            typed.sweep_surface,
            context.call(typed.circle_curve, radius / 2),
            context.call(typed.circle_curve, radius + 1),
            scale=radius,
            trihedron=typed.SweepTrihedron.CORRECTED_FRENET,
        ),
        typed.Surface,
    )
    spine = context.call(typed.circle_curve, radius + 1)
    scale_law = assert_type(
        context.call(typed.constant_sweep_scale, radius, spine.range()),
        typed.SweepScaleLaw,
    )
    assert_type(
        typed.constant_sweep_scale(radius, spine.range()),
        typed.SweepScaleLaw,
    )
    section_law = assert_type(
        context.call(
            typed.evolved_sweep_section,
            context.call(typed.circle_curve, radius / 2),
            scale_law,
        ),
        typed.SweepSectionLaw,
    )
    location_law = assert_type(
        context.call(typed.sweep_location, spine, typed.SweepTrihedron.FRENET),
        typed.SweepLocationLaw,
    )
    assert_type(
        context.call(typed.sweep_surface_from_laws, section_law, location_law),
        typed.Surface,
    )
    assert_type(
        typed.evolved_sweep_section(section_law.section, scale_law),
        typed.SweepSectionLaw,
    )
    assert_type(typed.sweep_location(spine), typed.SweepLocationLaw)
    assert_type(typed.sweep_surface_from_laws(section_law, location_law), typed.Surface)
    assert_type(typed.sweep_surface(section_law.section, spine), typed.Surface)
    assert_type(scale_law.scale, typed.Scalar)
    assert_type(scale_law.domain, typed.Interval)
    assert_type(section_law.section, typed.Curve)
    assert_type(location_law.spine, typed.Curve)
    assert_type(location_law.trihedron, typed.SweepTrihedron)

    assert_type(cylinder.point(0, radius), typed.Point3)
    assert_type(cylinder.normal(0, radius), typed.Vector3)
    assert_type(cylinder.u_range(), typed.Interval)
    assert_type(cylinder.v_range(), typed.Interval)
    assert_type(cylinder.u_iso(radius), typed.Curve)
    assert_type(cylinder.v_iso(radius), typed.Curve)
    assert_type(
        cylinder.map(
            context.call(
                typed.segment2,
                context.call(typed.point2, 0, 0),
                context.call(typed.point2, radius, radius),
            )
        ),
        typed.Edge,
    )
    assert_type(sweep, typed.Surface)
