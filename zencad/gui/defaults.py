"""Application-level defaults shared by the ZenCad GUI entry points."""

SCRIPT_TEMPLATE = """#!/usr/bin/env python3
# coding: utf-8

from zencad import *

model = box(10)
display(model)
show()
"""

EVENT_LOOP_PULSE_MS = 100
DEFAULT_WINDOW_SIZE = (1100, 760)
DEFAULT_HORIZONTAL_SIZES = (430, 670)
DEFAULT_VERTICAL_SIZES = (540, 180)
MINIMUM_CONSOLE_HEIGHT = 120
