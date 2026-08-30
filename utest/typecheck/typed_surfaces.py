"""Static result contract for typed Surface handles and sweep adapters."""

from typing_extensions import assert_type

from zencad import _typed as typed


def surface_contract(runtime: typed.Runtime) -> None:
    shape = runtime.box(2)
    radius = shape.mass() / 4
    cylinder = assert_type(runtime.cylinder_surface(radius), typed.Surface)
    sweep = assert_type(
        runtime.sweep_surface(
            runtime.circle_curve(radius / 2),
            runtime.circle_curve(radius + 1),
            scale=radius,
            trihedron=typed.SweepTrihedron.CORRECTED_FRENET,
        ),
        typed.Surface,
    )

    assert_type(cylinder.point(0, radius), typed.Point3)
    assert_type(cylinder.normal(0, radius), typed.Vector3)
    assert_type(cylinder.u_range(), typed.Interval)
    assert_type(cylinder.v_range(), typed.Interval)
    assert_type(cylinder.u_iso(radius), typed.Curve)
    assert_type(cylinder.v_iso(radius), typed.Curve)
    assert_type(cylinder.unlazy(), typed.Surface)
    assert_type(sweep, typed.Surface)
