#!/usr/bin/env python3
"""Headless STL, STEP, and 3MF export to binary streams."""
from zencad import *

import io



shape = box(20) - cylinder(4, 20).move(10, 10, 0)
stl = io.BytesIO()
step = io.BytesIO()
three_mf = io.BytesIO()

export_stl(shape, stl, binary=True)
export_step(shape, step, unit="mm")
export_3mf(shape, three_mf, name="Headless bracket")

assert len(stl.getvalue()) > 84
assert step.getvalue().startswith(b"ISO-10303-21")
assert three_mf.getvalue().startswith(b"PK")

display(shape, color=green)
show()
