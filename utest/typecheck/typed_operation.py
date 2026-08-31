"""Static contract for decorator-declared typed operations."""

from typing_extensions import assert_type

from zencad import _typed as typed


def operation_contract(runtime: typed.Runtime) -> None:
    direct = assert_type(typed.box(1, 2, 3), typed.Solid)
    forwarded = assert_type(runtime.box(1, 2, 3), typed.Solid)

    assert_type(direct + forwarded, typed.Shape)
    assert_type(direct.mass() + 1, typed.Scalar)
