#!/usr/bin/env python3
"""Headless STL, STEP, and 3MF export to binary streams."""

import io

import zencad


shape = zencad.box(20) - zencad.cylinder(4, 20).move(10, 10, 0)
stl = io.BytesIO()
step = io.BytesIO()
three_mf = io.BytesIO()

zencad.export_stl(shape, stl, binary=True)
zencad.export_step(shape, step, unit="mm")
zencad.export_3mf(shape, three_mf, name="Headless bracket")

assert len(stl.getvalue()) > 84
assert step.getvalue().startswith(b"ISO-10303-21")
assert three_mf.getvalue().startswith(b"PK")

zencad.display(shape, color=zencad.green)
zencad.show()
