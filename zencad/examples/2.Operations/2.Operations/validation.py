#!/usr/bin/env python3
"""Structured validation with explicit cleanup and healing."""
from zencad import *

import json



source = box(10) + box(10).right(10)
report = source.validate()
assert report.valid
print(json.dumps(report.to_dict(), sort_keys=True))

cleaned = source.clean()
healed = cleaned.heal()
healed.assert_valid()

display(source.left(12), color=yellow)
display(healed.right(12), color=green)
show()
